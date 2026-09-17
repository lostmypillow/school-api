import contextlib
import logging
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from src.config import settings

Base = declarative_base()
logger = logging.getLogger("rich")

class DatabaseSessionManager:  # noqa: D101
    def __init__(self) -> None:
        self.manager_id = str(uuid.uuid4())
        logger.info(f"DatabaseSessionManager initialized with ID: {self.manager_id}")

        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(self) -> None:
        """Initialize the async engine and sessionmaker."""
        self._engine = create_async_engine(
            URL.create(
                "mssql+aioodbc",
                username=settings.DB_USERNAME,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                database=settings.DB_NAME,
                query={
                    "driver": "ODBC Driver 18 for SQL Server",
                    "TrustServerCertificate": "yes",
                },
            ),
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,  # avoids detached object errors during tests
        )

    async def close(self) -> None:
        """
        Dispose of the engine safely.

        In tests, this may be called during pytest teardown when the event loop is closing,
        so failures are ignored gracefully.
        """
        if self._engine:
            try:  # noqa: SIM105
                await self._engine.dispose()
            except RuntimeError:
                # Ignore event-loop-closed errors during test teardown
                pass
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:  # noqa: D102
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")  # noqa: EM101
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        session = self._sessionmaker()
        session_id = str(uuid.uuid4())


        try:
            yield session
        except Exception:
            logger.warning(f"[{self.manager_id}] Session {session_id} rollback on error.")
            await session.rollback()
            raise
        finally:
            await session.close()


    @contextlib.asynccontextmanager
    async def session_with_transaction(self) -> AsyncIterator[AsyncSession]:
        """
        Session context manager with automatic rollback.

        - For tests, ensures DB state is clean after each test.
        - For production, behaves like a transaction scope.
        """
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        transaction = None

        try:
            transaction = await session.begin()
            yield session
        except Exception:
            if transaction:
                await transaction.rollback()
            raise
        finally:
            # Ensure rollback if transaction is still active
            if transaction and transaction.is_active:
                await transaction.rollback()
            await session.close()

    # Helpers for test DB setup
    async def create_all(self, connection: AsyncConnection):
        await connection.run_sync(Base.metadata.create_all)

    async def drop_all(self, connection: AsyncConnection):
        await connection.run_sync(Base.metadata.drop_all)


# Global instance
sessionmanager = DatabaseSessionManager()

