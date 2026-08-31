import logging

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.ntut import router as ntut_router
from app.omdb import router as omdb_router

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI()

origins = ["http://localhost:5173", "https://search.lostmypillow.com"]

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}


app.include_router(ntut_router)
app.include_router(omdb_router)
