# main.py

import logging
import os
import tomllib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Coroutine, cast
import fcntl
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse

from app.database.dependecies import get_session_ctx
from app.database.engine import async_engine
from app.features.card.router import router as card_router
from app.features.ldap.routers.ldap_router import router as ldap_router
from app.features.ldap.services.ldap_service import LdapService
from app.features.trials.router import router as submission_router

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



async def scheduled_ldap_sync() -> None:
    """Job that runs every day at 7pm."""
    async with get_session_ctx() as session:
        ldap_service = LdapService(session=session)
        await ldap_service.sync_all_users()


# noinspection PyUnusedLocal,PyShadowingNames
@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    # Only attempt lock if not in DEV mode
    if os.getenv("DEV") != "true":
        # Keep the file handle alive to maintain the lock
        app.state.lock_file = open("scheduler.lock", "wb")
        try:
            # LOCK_EX: Exclusive lock, LOCK_NB: Non-blocking
            fcntl.flock(app.state.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # This block only runs in the worker that gets the lock
            app.state.scheduler = AsyncIOScheduler()
            app.state.scheduler.add_job(scheduled_ldap_sync, "cron", hour=19, minute=0)
            app.state.scheduler.start()
            logger.info("Scheduler started successfully in this worker.")

        except BlockingIOError:
            logger.info("Another worker is already running the scheduler.")
            app.state.scheduler = None
    else:
        logger.info("Development mode: scheduler skipped.")
    yield
    if async_engine:
        logger.debug("async_engine is valid, awaiting disposal")
        await async_engine.dispose()
        logger.debug("async engine disposed")
    logger.info("internal-api shutdown complete.")


backend_pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)

is_linux = os.name == "posix" and os.uname().sysname == "Linux"

common_args = {
    "lifespan": lifespan,
    "title": backend_data.get("project", {}).get("name", "Kw FastAPI Project"),
    "description": backend_data.get("project", {}).get(
        "description",
        "description here",
    ),
    "version": backend_data.get("project", {}).get("version", "0.0.0"),
}

if is_linux:
    common_args.update(
        {
            "docs_url": None,
            "redoc_url": None,
            "root_path": "/api/v2",
        },
    )

app = FastAPI(**common_args)
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
async def custom_swagger_ui_html() -> HTMLResponse:
    """提供自架設的 Swagger 文件頁面.

    此函式依照以下指南進行設定, 將 Swagger 的 JS 與 CSS 資源自架並建立對應路由:
    https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/#self-hosting-javascript-and-css-for-docs

    Returns
    -------
    HTMLResponse
        Swagger API 文件頁面.

    .. attention::
    **為什麼要這樣設定 openapi_url, 而不是直接使用 `app.openapi_url`?**

    假設我們在 Linux 上部署, FastAPI 實例的 root_path 是 '/api/touch', 那麼 Swagger 所依賴的 openapi.json 就會被提供在 `http://IP_OR_DOMAIN/api/touch/openapi.json`. 但 `app.openapi_url` 的預設值是 `/openapi.json`, 如果完全照官方指南設定, Swagger 就會報錯, 因為它會去抓 `http://IP_OR_DOMAIN/openapi.json` 的 API 定義. 因此我們必須手動加上 root_path, 讓 Swagger 正確取得 `http://IP_OR_DOMAIN/api/touch/openapi.json`.

    .. todo::
        - 在 `tutor-api` 中, 這段程式碼與 `app.main.swagger_ui_redirect` 已被整合並移至單一模組 `app.api.docs` 中.

    
    """  # noqa: E501
    return get_swagger_ui_html(
        openapi_url=app.root_path + cast("str", app.openapi_url),
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/swagger_assets/swagger-ui-bundle.js",
        swagger_css_url="/swagger_assets/swagger-ui.css",
        swagger_favicon_url="/swagger_assets/favicon.ico",
    )


@app.get(cast("str", app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    """老實說我不知道這段程式碼的用途.

    但它出現在我所參考的官方指南中:
    https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/#self-hosting-javascript-and-css-for-docs.

    Returns
    -------
    HTMLResponse
        目前用途不明.

    .. todo::
        - 如果你看到這裡, 而且**知道**這段是做什麼的, 請幫忙更新這份 docstring.
        - 重構建議請參考 `app.main.custom_swagger_ui_html`.

    
    """
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(ldap_router)
app.include_router(card_router)
app.include_router(submission_router)
