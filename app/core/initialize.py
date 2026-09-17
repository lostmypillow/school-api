import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
os.makedirs(DATA_DIR, exist_ok=True)


class DB:
    def __init__(self, db_url: str):
        # 1. Handle driver-specific connect args
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
