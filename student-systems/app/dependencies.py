from bs4.element import Tag
from bs4.element import ResultSet
import asyncio
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.models import Base
from app.schemas import ServerErrorDetail, ServerErrorLog

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_URL = os.getenv("DB_URL", f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.db'}")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
os.makedirs(DATA_DIR, exist_ok=True)


@asynccontextmanager
async def get_db_session(
    factory: async_sessionmaker | None = None,
    app: FastAPI | None = None,
) -> AsyncGenerator[AsyncSession]:
    """Pure context manager that accepts a factory directly or extracts it from an app instance."""
    if factory is None and app is not None:
        factory = app.state.sessionfactory

    if factory is None:
        raise ValueError(
            "Either a sessionfactory or app instance must be provided to get_db_session()"
        )

    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session_dependency(
    request: Request,
) -> AsyncGenerator[AsyncSession]:
    """FastAPI route dependency wrapper that pulls factory from the request app state."""
    async with get_db_session(factory=request.app.state.sessionfactory) as session:
        yield session



def create_db_factory(db_url: str):
    connect_args = (
        {"check_same_thread": False} if db_url.startswith("aiosqlite") else {}
    )

    engine = create_async_engine(db_url, connect_args=connect_args, pool_pre_ping=True)

    session_factory = async_sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )
    return engine, session_factory



class CustomAsyncClient(httpx.AsyncClient):
    __slots__ = ("semaphore",)

    def __init__(self, *args, max_concurrency: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore = asyncio.Semaphore(max_concurrency)

_client: CustomAsyncClient | None = None


def get_scrape_client(max_concurrency: int = 20) -> CustomAsyncClient:
    """Returns the existing global client or creates a new one."""
    global _client
    if _client is None or _client.is_closed:
        limits = httpx.Limits(
            max_connections=max_concurrency, max_keepalive_connections=10
        )
        _client = CustomAsyncClient(
            verify=False, limits=limits, timeout=10.0, max_concurrency=max_concurrency
        )
    return _client


async def close_scrape_client():
    """Call this on application shutdown to close connections cleanly."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def scrape(url: str, tag: str):
    """Scrapes using the shared internal HTTP client with error handling."""
    
    client = get_scrape_client()
    async with client.semaphore:
        combined_url = "https://aps.ntut.edu.tw/course/tw/" + url
        bs4_mode = "html.parser" if tag == "sem" else "lxml"

        if tag == "sem":
            bs4_function = lambda t: t.name == "a" and t.get("href", "").startswith("Subj")
        else:
            bs4_function = tag

        try:
            response = await client.get(combined_url)
            response.raise_for_status()
            return BeautifulSoup(response.text, bs4_mode).find_all(bs4_function)

        except httpx.HTTPError as exc:
            error_id = str(uuid.uuid4())
            # logger.exception(
            #     ServerErrorLog(
            #         reference_id=error_id, message="httpx had an error", detail=str(exc)
            #     ).model_dump(mode="json")
            # )
            return BeautifulSoup("<error></error>", bs4_mode).find_all("error")

        except Exception as e:
            error_id = str(uuid.uuid4())
            # logger.error(
            #     ServerErrorLog(
            #         reference_id=error_id, message="Undefined error", detail=str(e)
            #     ).model_dump(mode="json")
            # )
            return BeautifulSoup("<error></error>", bs4_mode).find_all("error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_scrape_client()
    engine, session_factory = create_db_factory(DB_URL)

    app.state.db_engine = engine
    app.state.sessionfactory = session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.arq_redis = await create_pool(
        RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    )

    yield
    await engine.dispose()
    await app.state.arq_redis.close()
    await close_scrape_client()
