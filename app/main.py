import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from redis_fastapi import FastAPIRedis

from app.core.initialize import DB
from app.core.models import Base

from app.domains.courses import router as course_router
from app.domains.sync import router as sync_router
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"sqlite+aiosqlite:///{DATA_DIR / 'ntut_bootstrap.db'}")
    app.state.db = DB(os.getenv("DB_URL", ""))

    async with app.state.db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("here")

    app.state.arq_redis = await create_pool(
        RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    )

    yield
    await app.state.db.close()
    await app.state.arq_redis.close()


app = FastAPI(title="School API", version="4.0.1", lifespan=lifespan)


origins = ["http://localhost:5173", "http://localhost:8081", "http://localhost:8000", "https://school.lostmypillow.com", "https://school-dev.lostmypillow.com"]

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check(req: Request):
    logger.info(req.app.state.db_engine)
    return {"status": "healthy"}


app.include_router(course_router)
app.include_router(sync_router)
FastAPIRedis(app).lifespan().caching()
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_URL = os.getenv("DB_URL", "")
