import logging
import os
from contextlib import asynccontextmanager

import fastapi
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from redis_fastapi import FastAPIRedis
from rq import Queue

from app.core.exec_sql import init_db, close_db
from app.domains.courses import router as course_router
from app.domains.courses.tasks import bootstrap_mssql_task
from app.domains.tutor import router as tutor_router

load_dotenv()
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)



@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    await init_db()
    fastapi_app.state.redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    fastapi_app.state.queue = Queue(connection=fastapi_app.state.redis)
    fastapi_app.state.queue.enqueue(bootstrap_mssql_task, job_timeout=1000)
    yield
    fastapi_app.state.redis.close()
    await close_db()



app = FastAPI(title="School API", version="5.1.0", lifespan=lifespan)


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
app.include_router(tutor_router)

FastAPIRedis(app).lifespan().caching()
