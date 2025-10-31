# main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI

import logging
from app.features.ldap.routers.ldap_router import router as ldap_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup complete.")
    yield
    logger.info("Application shutdown complete.")

app = FastAPI(
    title="內部API v2",
    description=" Internal API with integrated features in one monolith instead of repo per feature",
    version="2.0.0-beta",
    lifespan=lifespan
)

app.include_router(ldap_router)