import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.tables.base_model import Base
from app.domains.courses.router import router as courses_router


class DB:
    """Test helper DB class providing async session management."""

    def __init__(self, db_url: str):
        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        self.engine: AsyncEngine = create_async_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )

        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        await self.engine.dispose()


class MockRedis:
    """In-memory mock for Redis client."""

    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str | bytes, ex: int | None = None):
        self.store[key] = value

    async def close(self):
        pass


class MockHTTPClient:
    """Mock for CustomAsyncClient."""

    def __init__(self, responses: dict[str, str] | None = None, default_response: str = "<html><body></body></html>"):
        self.is_closed = False
        self.semaphore = asyncio.Semaphore(10)
        self.responses = responses or {}
        self.default_response = default_response
        self.get_mock = AsyncMock()

    async def get(self, url: str):
        if url in self.responses:
            mock_resp = MagicMock()
            mock_resp.text = self.responses[url]
            mock_resp.raise_for_status = MagicMock()
            return mock_resp
        if self.get_mock.side_effect is not None:
            return await self.get_mock(url)
        if self.get_mock.return_value is not None and not isinstance(self.get_mock.return_value, AsyncMock):
            return await self.get_mock(url)
        mock_resp = MagicMock()
        mock_resp.text = self.default_response
        mock_resp.raise_for_status = MagicMock()
        await self.get_mock(url)
        return mock_resp

    async def aclose(self):
        pass


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Provides a fresh SQLite in-memory AsyncEngine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _register_sqlite_functions(dbapi_connection, connection_record):
        dbapi_connection.create_function(
            "SYSDATETIMEOFFSET", 0, lambda: datetime.now(UTC).isoformat()
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine: AsyncEngine) -> DB:
    """Provides a DB instance wrapped around the test engine."""
    db = DB.__new__(DB)
    db.engine = test_engine
    db.session_factory = async_sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    return db


@pytest_asyncio.fixture
async def test_session(test_db: DB) -> AsyncGenerator[AsyncSession, None]:
    """Yields a database session from the test DB."""
    async with test_db.get_session() as session:
        yield session


@pytest.fixture
def mock_redis() -> MockRedis:
    return MockRedis()


@pytest.fixture
def mock_client() -> MockHTTPClient:
    return MockHTTPClient()


@pytest_asyncio.fixture
async def app_client(test_db: DB) -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient targeting a test FastAPI app with courses router."""
    app = FastAPI()

    # Override cache dependencies to bypass Redis in route tests
    async def dummy_cache_dep():
        yield

    for route in courses_router.routes:
        for dep in getattr(route, "dependencies", []):
            app.dependency_overrides[dep.dependency] = dummy_cache_dep

    app.include_router(courses_router)
    app.state.db = test_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def temp_parquet_dir(tmp_path):
    parquet_dir = tmp_path / "parquet_data"
    parquet_dir.mkdir(parents=True, exist_ok=True)
    return parquet_dir


