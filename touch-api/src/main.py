import tomllib
from contextlib import asynccontextmanager
from pathlib import Path as pathlib_Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from typing import cast
from .routers import (
    ws,
    auth,
    seat,
    survey,
    status,
)
import os
from .database.exec_sql import async_engine

from rich.logging import RichHandler
from rich.traceback import install
import logging

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
    


    yield
    if async_engine:
        await async_engine.dispose()
        logger.info("[SHUTDOWN] Disposed async SQLAlchemy Engine")


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
            "root_path": "/api/touch",
        }
    )

app = FastAPI(**common_kwargs)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.root_path + cast(str, app.openapi_url),
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/swagger_assets/swagger-ui-bundle.js",
        swagger_css_url="/swagger_assets/swagger-ui.css",
        swagger_favicon_url="/swagger_assets/favicon.ico",
    )


@app.get(cast(str, app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(status.router)

app.include_router(auth.router)

app.include_router(ws.router)

app.include_router(seat.router)

app.include_router(survey.router)
