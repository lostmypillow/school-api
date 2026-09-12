import os
from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI

from app.db.initialize import DB
from app.db.models import Base

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DB_URL = os.getenv("DB_URL", "")


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.db = DB(f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.db'}")
    print(f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_boostrap.db'}")

    async with app.state.db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("here")

    app.state.arq_redis = await create_pool(
        RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    )

    yield
    await app.state.db.close()
    await app.state.arq_redis.close()
