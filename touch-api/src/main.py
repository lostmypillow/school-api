from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .config import settings
from pprint import pprint
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.routers.ws import ws_router, send_updates
from src.routers.auth import auth_router
from src.routers.picture import picture_router
from src.routers.seat import seat_router
from src.routers.survey import survey_router
from src.database.exec_sql import async_engine, exec_sql
import logging
logger = logging.getLogger('uvicorn.error')
from .version import VERSION






async def lifespan(app: FastAPI):
    logger.info(f"KwTouchscreen v{VERSION} starting...")
    logger.info("Starting AsyncIOScheduler...")
    scheduler = AsyncIOScheduler()
    scheduler.start()
    scheduler.add_job(
        send_updates,
        "interval",
        seconds=5
    )

    yield
    if async_engine:
        await async_engine.dispose()
        logger.info('[SHUTDOWN] Disposed async SQLAlchemy Engine')

    if scheduler:
        scheduler.shutdown()
        logger.info('[SHUTDOWN] Shut down APScheduler')


app = FastAPI(
    lifespan=lifespan,
    title="",
    version=VERSION, # Synced with latest frontend version
    swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}}
    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(picture_router)

app.include_router(auth_router)

app.include_router(ws_router)

app.include_router(seat_router)

app.include_router(survey_router)

app.mount("/touch", StaticFiles(directory="public", html=True), name="dash")