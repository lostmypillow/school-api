"""FastAPI 入口檔案.

依照 `src.main` 原始碼自上而下的順序:

1. 定義 `src.main.lifespan`.
2. 從 `pyproject.toml` 中擷取標題 (key 為 'name')、描述與版本.
3. 將上述資訊與鍵 'lifespan' 和值 `src.main.lifespan` 一起組成 `common_kwargs` 字典.
4. 如果此 FastAPI 正在 Linux 上部署, 則停用內建 Swagger、ReDoc 並更新 root_path.這假設開發發生於 Windows, 而部署則在 Linux 上.那現在的問題是: 我在 production 中還能存取 `http://IP_OR_DOMAIN/api/touch/docs` 嗎?
> 解答: 其實我們在 "/docs" 路徑上提供了自定義的 Swagger, 使用的是 `src.main.custom_swagger_ui_html`.
5. 將合併後的 kwargs 傳入 FastAPI.
6. 定義 `src.main.custom_swagger_ui_html` 與 `src.main.swagger_ui_redirect`.
7. 使用 `include_router` 函式將所有路由加入 FastAPI.

.. todo::
    - 強制設定 CORS: 目前在加上 CORSMiddleware 時, allow_origins 被設為 `["*"]`, 這是**不安全**的, 應改為 `["FRONTEND_URL"]`. 詳情請見: https://fastapi.tiangolo.com/tutorial/cors/.
    - 步驟 2 到 4: 在 `` refactor branch 中, 這些步驟已被移到 `app.core.config` 模組中, 並從該模組匯入字典後傳入 FastAPI 作為 kwargs.請參考 `` refactor branch 的 `app.core.config` 模組來了解如何重構.


"""  # noqa: E501

import logging
import os
import tomllib
from contextlib import asynccontextmanager
from pathlib import Path as pathlib_Path
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from rich.logging import RichHandler
from rich.traceback import install

from src.database.exec_sql import sessionmanager
from src.routers import (
    auth,
    seat,
    status,
    survey,
    ws,
)

logger = logging.getLogger("rich")


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """設定 Rich logger. 在 FastAPI 關閉時釋放 SQLAlchemy 的 async_engine.

    Parameters
    ----------
    app : FastAPI
        FastAPI 類別, 請參見 https://fastapi.tiangolo.com/reference/fastapi/

    .. todo::
        - 在 `` refactor branch 中, 這整個函式 (包含 @asynccontextmanager 裝飾器)已被移至 `app.core.lifespan`.
        - 至於為什麼是 "app" 而不是 "src", 請參見 `src` 的說明.
        - 此外, 在 `` refactor branch 中, 所有日誌記錄邏輯也都已重構並移至 `app.core.log`, 詳情請見該專案的 `app.core.log` 模組.

    
    """  # noqa: E501
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
    sessionmanager.init()

    yield
    await sessionmanager.close()
    logger.info("[SHUTDOWN] Disposed async SQLAlchemy Engine")


backend_pyproject_path = pathlib_Path(__file__).resolve().parent.parent / "pyproject.toml"
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)

is_linux = os.name == "posix" and os.uname().sysname == "Linux"

common_kwargs = {
    "lifespan": lifespan,
    "title": backend_data.get("project", {}).get("name", "Kw FastAPI Project"),
    "description": backend_data.get("project", {}).get(
        "description",
        "description here",
    ),
    "version": backend_data.get("project", {}).get("version", "0.0.0"),
}

if is_linux:
    common_kwargs.update(
        {
            "docs_url": None,
            "redoc_url": None,
            "root_path": "/api/touch",
        },
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
        - 在 `` refactor branch 中, 這段程式碼與 `src.main.swagger_ui_redirect` 已被整合並移至單一模組 `app.api.docs` 中. - 至於為什麼最上層模組名稱是 `app` 而不是 `src`, 請參考 `src` 的說明.

    
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
        - 重構建議請參考 `src.main.custom_swagger_ui_html`.

    *由 林家民 於 2025/7/17 撰寫, 原文為自己寫的英文, 由 ChatGPT 翻譯為繁體中文. *
    """
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(status.router)

app.include_router(auth.router)

app.include_router(ws.router)

app.include_router(seat.router)

app.include_router(survey.router)
