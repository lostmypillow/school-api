from app.domains.tutor.routers import announcement_router, ws_router, update_router, card_router
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from mssql_python.pooling import PoolingManager
from redis import Redis
from redis_fastapi import FastAPIRedis
from rq import Queue
from app.domains.tasks.bootstrap_mssql import bootstrap_mssql
from app.domains.courses import router as course_router
from app.domains.tasks import router as tasks_router

load_dotenv()
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)



@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    if not PoolingManager.is_enabled():
        PoolingManager.enable(max_size=50, idle_timeout=600)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = Redis.from_url(redis_url)
    fastapi_app.state.redis = redis_conn
    fastapi_app.state.rq_redis = redis_conn
    fastapi_app.state.rq_queue = Queue(connection=fastapi_app.state.redis)
    fastapi_app.state.rq_queue.enqueue(bootstrap_mssql)

    yield
    if PoolingManager.is_enabled():
        PoolingManager.disable()
    fastapi_app.state.redis.close()


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
    logger.info(getattr(req.app.state, "db_engine", getattr(req.app.state, "db", None)))
    return {"status": "healthy"}


app.include_router(course_router)
app.include_router(tasks_router)
app.include_router(announcement_router)
app.include_router(ws_router)
app.include_router(update_router)
app.include_router(card_router)


FastAPIRedis(app).lifespan().caching()