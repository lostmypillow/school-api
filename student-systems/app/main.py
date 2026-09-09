import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from redis_fastapi import FastAPIRedis

from app.dependencies import lifespan
from app.ntut import router as ntut_router
from app.omdb import router as omdb_router

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


app = FastAPI(version="2.1.0-SNAPSHOT", lifespan=lifespan)

FastAPIRedis(app).lifespan()

origins = ["http://localhost:5173", "https://search.lostmypillow.com"]

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


app.include_router(ntut_router)
app.include_router(omdb_router)
