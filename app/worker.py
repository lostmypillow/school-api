import asyncio
import hashlib
import logging
import os
import traceback
import uuid
from pathlib import Path

import httpx
from arq import ArqRedis
from arq.connections import RedisSettings
from bs4 import BeautifulSoup

from app.core.database.initialize import DB
from app.domains.courses.bootstrap_sqlite import bootstrap_sqlite
from sqlalchemy import text
from dotenv import load_dotenv
from app.domains.courses.bootstrap_mssql import bootstrap_mssql

load_dotenv()
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


async def startup(ctx: dict):
    bootstrap_engine = DB(os.getenv("BOOTSTRAP_URL", "")).engine

    async with bootstrap_engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        result = await conn.execute(
            text("SELECT name FROM sys.databases WHERE name = 'student_db'")
        )
        db_exists = result.scalar()

        if not db_exists:
            print("Database 'student_db' not found. Creating...")
            await conn.execute(text("CREATE DATABASE student_db"))
            print("Database 'student_db' created successfully.")

    await bootstrap_engine.dispose()
    print((f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.database'}"))
    ctx["database"] = DB(f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.database'}")
    ctx["mssql_db"] = DB(os.getenv("DB_URL", ""))
    ctx["client"] = get_scrape_client()
    print("ARQ Worker initialized database engine.")


async def shutdown(ctx: dict):
    await close_scrape_client()
    if ctx["database"]:
        await ctx["database"].close()
        print("SQLite database engine disposed.")
    if ctx["mssql_db"]:
        await ctx["mssql_db"].close()
        print("MSSQL database engine disposed.")


class WorkerSettings:
    functions = [bootstrap_sqlite, bootstrap_mssql]
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    max_jobs = 10
    job_timeout = 3000
    on_startup = startup
    on_shutdown = shutdown


logger = logging.getLogger(__name__)


class CustomAsyncClient(httpx.AsyncClient):
    __slots__ = ("semaphore",)

    def __init__(self, *args, max_concurrency: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = asyncio.Semaphore(max_concurrency)


_client: CustomAsyncClient | None = None


def get_scrape_client(max_concurrency: int = 10) -> CustomAsyncClient:
    """Returns the existing global client or creates a new one."""
    global _client
    if _client is None or _client.is_closed:
        limits = httpx.Limits(
            max_connections=max_concurrency, max_keepalive_connections=10
        )
        _client = CustomAsyncClient(
            verify=False, limits=limits, timeout=30.0, max_concurrency=max_concurrency
        )
    return _client


async def close_scrape_client():
    """Call this on application shutdown to close connections cleanly."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def fetch_html(
    ctx,
    redis: ArqRedis,
    combined_url: str,
    ttl_seconds: int = 86400,
) -> str:
    """Fetches raw HTML from Redis cache, or falls back to HTTP request on miss."""
    url_hash = hashlib.sha256(combined_url.encode("utf-8")).hexdigest()
    cache_key = f"cache:html:{url_hash}"

    # 1. Try reading from Redis cache
    cached_val = await redis.get(cache_key)
    if cached_val is not None:
        if isinstance(cached_val, bytes):
            return cached_val.decode("utf-8")
        return cached_val
    client: CustomAsyncClient = ctx["client"]  #
    # 2. Fetch from network on cache miss
    response = await client.get(combined_url)
    response.raise_for_status()
    html_text = response.text

    # 3. Save response string to Redis with TTL
    await redis.set(cache_key, html_text, ex=ttl_seconds)
    return html_text


async def scrape(ctx: dict, url: str, tag: str):
    """Scrapes using the shared internal HTTP client with error handling and Redis caching.

    Designed for use as an arq task accepting `ctx` containing `redis`.
    """
    redis: ArqRedis = ctx["redis"]
    client: CustomAsyncClient = ctx["client"]  #

    async with client.semaphore:
        combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
        bs4_mode = "html.parser" if tag == "sem" else "lxml"

        if tag == "sem":

            def bs4_function(t):
                return t.name == "a" and t.get("href", "").startswith("Subj")
        else:
            bs4_function = tag

        try:
            # Fetch from Redis cache or network
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
