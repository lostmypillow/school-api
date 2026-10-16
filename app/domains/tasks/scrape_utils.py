import asyncio
import hashlib
import inspect
import traceback
import uuid
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.core.custom_http_client import CustomAsyncClient


async def fetch_html(
    ctx: dict[str, Any],
    redis: Any | None,
    combined_url: str,
    ttl_seconds: int = 86400,
    max_retries: int = 3,
) -> str:
    cache_key: str = ''
    html_text: str = ''
    """Fetches raw HTML from Redis cache if available, or falls back to HTTP request with retries."""
    if redis is not None:
        url_hash: str = hashlib.sha256(combined_url.encode("utf-8")).hexdigest()
        cache_key = f"cache:html:{url_hash}"

        cached_val = redis.get(cache_key)
        if inspect.isawaitable(cached_val):
            cached_val = await cached_val

        if cached_val is not None:
            if isinstance(cached_val, bytes):
                return cached_val.decode("utf-8")
            return cached_val

    for attempt in range(max_retries):
        try:
            response = await ctx["client"].get(combined_url)
            response.raise_for_status()
            html_text = response.text
            break
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
            last_exc: httpx.ConnectError | httpx.ConnectTimeout | httpx.ReadTimeout = exc
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (2**attempt))
            else:
                raise last_exc

    if redis is not None:
        set_result = redis.set(cache_key, html_text, ex=ttl_seconds)
        if inspect.isawaitable(set_result):
            await set_result
    return html_text


async def scrape(ctx: dict[str, Any], url: str, tag: str) -> list[Any]:
    """Scrapes using the shared internal HTTP client with error handling and Redis caching."""
    redis = ctx.get("redis")
    client: CustomAsyncClient = ctx["client"]

    async with client.semaphore:
        combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
        bs4_mode = "html.parser" if tag == "sem" else "lxml"

        if tag == "sem":

            def bs4_function(t: Any) -> bool:
                return t.name == "a" and t.get("href", "").startswith("Subj")
        else:
            bs4_function = tag

        try:
            html_text = await fetch_html(ctx, redis, combined_url)
            return BeautifulSoup(html_text, bs4_mode).find_all(bs4_function)

        except httpx.HTTPError as exc:
            error_id = str(uuid.uuid4())
            req_info = (
                f"{exc.request.method} {exc.request.url}"
                if exc.request
                else "No request"
            )
            resp_info = ""
            if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                resp_info = f" | Status: {exc.response.status_code} | Body: {exc.response.text[:300]}"
            print(
                f"[ERROR ID {error_id}] [{type(exc).__name__}] {req_info}{resp_info} => {exc}"
            )
            print(traceback.format_exc())
            return BeautifulSoup("<error></error>", bs4_mode).find_all("error")

        except Exception as e:
            error_id = str(uuid.uuid4())
            print(f"[ERROR ID {error_id}] [{type(e).__name__}] => {e}")
            print(traceback.format_exc())
            return BeautifulSoup("<error></error>", bs4_mode).find_all("error")
