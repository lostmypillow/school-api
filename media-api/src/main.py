from rich.logging import RichHandler
from rich.traceback import install
import logging
import os
from fastapi import FastAPI

from src.config import settings
from typing import cast
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import tomllib
from pathlib import Path as pathlib_Path
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from src.dependencies import async_engine
from .routers import video, picture

# Static variables
# TODO move them to .env
SMB_URL = f"//{settings.SMB_HOST}{settings.SMB_FOLDER}"
SMB_USERNAME = settings.SMB_USERNAME
SMB_PASSWORD = settings.SMB_PASSWORD
CHUNK_SIZE = 512 * 1024  # 512 KB
STATIC_FOLDER = "./static"
video_cycler = None
from time import perf_counter
# Configure logging
logger = logging.getLogger("rich")

@asynccontextmanager
async def lifespan(app: FastAPI):
    install(show_locals=True)
    rich_handler = RichHandler(rich_tracebacks=True)
    logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[rich_handler],
        )
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
            logger = logging.getLogger(name)
            logger.handlers = [rich_handler]
            logger.setLevel(logging.INFO)
    logging.info("Starting app, syncing files from SMB...")
    yield
    if async_engine:
        await async_engine.dispose()
        logger.info("[SHUTDOWN] Disposed async SQLAlchemy Engine")
    logging.info("Shutting down app...")


backend_pyproject_path = (
    pathlib_Path(__file__).resolve().parent.parent / "pyproject.toml"
)
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)

is_linux = os.name == "posix" and os.uname().sysname == "Linux"

common_kwargs = {
    "lifespan": lifespan,
    "title": backend_data.get("project", {}).get("name", "Kw FastAPI Project"),
    "description": backend_data.get("project", {}).get(
        "description", "description here"
    ),
    "version": backend_data.get("project", {}).get("version", "0.0.0"),
}

if is_linux:
    common_kwargs.update(
        {
            "docs_url": None,
            "redoc_url": None,
            "root_path": "/api/media",
        }
    )

app = FastAPI(**common_kwargs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_local_filenames() -> list[str]:
    return [
        filename for filename in os.listdir(STATIC_FOLDER) if filename.endswith(".mp4")
    ]



@app.get("/docs", include_in_schema=False)

async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.root_path + cast(str, app.openapi_url),
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/api/tutor/static/swagger-ui-bundle.js",
        swagger_css_url="/api/tutor/static/swagger-ui.css",
        swagger_favicon_url="/api/tutor/static/favicon.ico",
    )


@app.get(cast(str, app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(video.router)
app.include_router(picture.router)