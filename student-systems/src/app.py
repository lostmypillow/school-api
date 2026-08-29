import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from src.ntut import router as ntut_router
from src.omdb import router as omdb_router

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI()

origins = ["http://localhost:5173", "https://search.lostmypillow.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(ntut_router)
app.include_router(omdb_router)
handler = Mangum(app)
