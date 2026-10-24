from os import getenv
from asyncio import Semaphore

from httpx import AsyncClient, Response

import asyncio
import hashlib
import inspect
import traceback
import uuid
from typing import Any
from redis import Redis

import httpx
from bs4 import BeautifulSoup


class CustomAsyncClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self.semaphore: Semaphore = Semaphore(20)
        self.redis: Redis = Redis.from_url(
            f"redis://{getenv("REDIS_HOST", "localhost")}:6379/0"
        )

    def _ensure_active_client(self) -> AsyncClient | None:
        """Creates or revives the client on the current active event loop."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=False,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=10),
                timeout=30.0,
            )
            self.semaphore = Semaphore(20)
        return self._client

    async def fetch_html(
        self,
        combined_url: str,
    ) -> str:
        redis = self.redis
        cache_key: str = ""
        html_text: str = ""
        """Fetches raw HTML from Redis cache if available, or falls back to HTTP request with retries."""
        self._ensure_active_client()
        assert self._client is not None
        if redis is not None:
            cached_val = redis.get(
                f"cache:html:{hashlib.sha256(combined_url.encode('utf-8')).hexdigest()}"
            )
            if inspect.isawaitable(cached_val):
                cached_val = await cached_val

            if cached_val is not None:
                if isinstance(cached_val, bytes):
                    return cached_val.decode("utf-8")
                return cached_val

        for attempt in range(3):
            try:
                response: Response = await self._client.get(combined_url)
                response.raise_for_status()
                html_text: str = response.text
                break
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                last_exc: (
                    httpx.ConnectError | httpx.ConnectTimeout | httpx.ReadTimeout
                ) = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (2**attempt))
                else:
                    raise last_exc

        if redis is not None:
            set_result = redis.set(cache_key, html_text, ex=86400)
            if inspect.isawaitable(set_result):
                await set_result
        return html_text

    async def scrape(self, url: str, tag: str) -> list[Any]:
        """Scrapes using the shared internal HTTP client with error handling and Redis caching."""

        async with self.semaphore:
            combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
            bs4_mode = "html.parser" if tag == "sem" else "lxml"

            if tag == "sem":

                def bs4_function(t: Any) -> bool:
                    return t.name == "a" and t.get("href", "").startswith("Subj")
            else:
                bs4_function = tag

            try:
                html_text = await self.fetch_html(combined_url=combined_url)
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
                return BeautifulSoup(
                    markup="<error></error>", features=bs4_mode
                ).find_all("error")

            except Exception as e:
                error_id = str(uuid.uuid4())
                print(f"[ERROR ID {error_id}] [{type(e).__name__}] => {e}")
                print(traceback.format_exc())
                return BeautifulSoup(
                    markup="<error></error>", features=bs4_mode
                ).find_all("error")

    async def aclose(self) -> None:
        """Closes the active transport if open."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()


client = CustomAsyncClient()
