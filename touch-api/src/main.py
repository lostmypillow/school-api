from .version import VERSION
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import tomllib
from .routers import (
    ws_router,
    auth_router,
    picture_router,
    seat_router,
    survey_router,
    status_router,
)
from .logger import logger
from .database.exec_sql import async_engine
from contextlib import asynccontextmanager
from pathlib import Path as pathlib_Path
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)



current_file = pathlib_Path(__file__).resolve()
backend_pyproject_path = current_file.parent.parent / "pyproject.toml"
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)
title = backend_data.get("project", {}).get("name", "Kw FastAPI Project")
version = backend_data.get("project", {}).get("version", "0.0.0")
description = backend_data.get("project", {}).get("description", "description here")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{title} v{version} starting...")
    yield
    if async_engine:
        await async_engine.dispose()
        logger.info("[SHUTDOWN] Disposed async SQLAlchemy Engine")


app = FastAPI(
    lifespan=lifespan,
    title=title,
    description=description,
    version=version,
    docs_url=None,
    redoc_url=None,
    root_path="/api/touch",
)

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
        openapi_url=app.root_path + app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/api/tutor/static/swagger-ui-bundle.js",
        swagger_css_url="/api/tutor/static/swagger-ui.css",
        swagger_favicon_url="/api/tutor/static/favicon.ico",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()



app.include_router(status_router)
app.include_router(picture_router)

app.include_router(auth_router)

app.include_router(ws_router)

app.include_router(seat_router)

app.include_router(survey_router)

# app.mount("/touch", StaticFiles(directory="public", html=True), name="dash")
