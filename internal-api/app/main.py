# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI

import logging

from app.database.dependecies import get_session
from app.database.engine import async_engine
from app.features.ldap.routers.ldap_router import router as ldap_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.features.ldap.services.ldap_service import LdapService

# Disable FastAPI CLI pretty logs & duplicate uvicorn logs
logging.getLogger("uvicorn.error").propagate = False
logging.getLogger("uvicorn.access").propagate = False
logging.getLogger("watchfiles.main").propagate = False  # optional: suppress dev file watcher logs

# Standard production-style logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def scheduled_ldap_sync():
    """Job that runs every day at 7pm."""
    async with get_session() as session:
        ldap_service = LdapService(session=session)
        await ldap_service.sync_all_users()

# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(scheduled_ldap_sync, "cron", hour=19, minute=0)
    scheduler.start()
    logger.info("Application startup complete.")
    yield
    if async_engine:
        await async_engine.dispose()
    logger.info("Application shutdown complete.")

app = FastAPI(
    title="內部API v2",
    description=" Internal API with integrated features in one monolith instead of repo per feature",
    version="2.0.0-beta",
    lifespan=lifespan
)

app.include_router(ldap_router)