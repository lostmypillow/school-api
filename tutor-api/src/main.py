"""FastAPI 入口檔案.

依照 `src.main` 原始碼自上而下的順序:

1. 定義 `src.main.lifespan`.
2. 從 `pyproject.toml` 中擷取標題 (key 為 'name')、描述與版本.
3. 將上述資訊與鍵 'lifespan' 和值 `src.main.lifespan` 一起組成 `common_kwargs` 字典.
4. 如果此 FastAPI 正在 Linux 上部署, 則停用內建 Swagger、ReDoc 並更新 root_path.這假設開發發生於 Windows, 而部署則在 Linux 上.那現在的問題是: 我在 production 中還能存取 `http://IP_OR_DOMAIN/api/touch/docs` 嗎?
> 解答: 其實我們在 "/docs" 路徑上提供了自定義的 Swagger, 使用的是 `src.main.custom_swagger_ui_html`.
5. 將合併後的 kwargs 傳入 FastAPI.
6. 定義 `src.main.custom_swagger_ui_html` 與 `src.main.swagger_ui_redirect`.
7. 之後問題太多了, 請見`src.main.determine_role` 的 docstring 以了解剩下的 todo.

.. todo::
    - 強制設定 CORS: 目前在加上 CORSMiddleware 時, allow_origins 被設為 `["*"]`, 這是**不安全**的, 應改為 `["FRONTEND_URL"]`. 詳情請見: https://fastapi.tiangolo.com/tutorial/cors/.
    - 步驟 2 到 4: 在 refactor branch 中, 這些步驟已被移到 `app.core.config` 模組中, 並從該模組匯入字典後傳入 FastAPI 作為 kwargs.請參考 refactor branch 的 `app.core.config` 模組來了解如何重構.


"""  # noqa: E501
import logging
import os
import tomllib
from contextlib import asynccontextmanager
from pathlib import Path as pathlib_Path
from typing import cast

from fastapi import FastAPI, WebSocket, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from rich.logging import RichHandler
from rich.traceback import install

from src.database.exec_sql import async_engine, exec_sql

from .models import Cardholder, Device
from .routers import announcement_router, sync_frontend, ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    """設定 Rich logger. 在 FastAPI 關閉時釋放 SQLAlchemy 的 async_engine.

    Parameters
    ----------
    app : FastAPI
        FastAPI 類別, 請參見 https://fastapi.tiangolo.com/reference/fastapi/

    .. todo::
        - 在 refactor branch 中, 這整個函式 (包含 @asynccontextmanager 裝飾器)已被移至 `app.core.lifespan`.
        - 至於為什麼是 "app" 而不是 "src", 請參見 `src` 的說明.
        - 此外, 在 refactor branch 中, 所有日誌記錄邏輯也都已重構並移至 `app.core.log`, 詳情請見該專案的 `app.core.log` 模組.

    
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
    yield
    if async_engine:
        await async_engine.dispose()


logger = logging.getLogger("rich")
backend_pyproject_path = pathlib_Path(__file__).resolve().parent.parent / "pyproject.toml"
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)

is_linux = os.name == "posix" and os.uname().sysname == "Linux"

common_kwargs = {
    "lifespan": lifespan,
    "title": backend_data.get("project", {}).get("name", "Kw FastAPI Project"),
    "description": backend_data.get("project", {}).get("description", "description here"),
    "version": backend_data.get("project", {}).get("version", "0.0.0"),
}

if is_linux:
    common_kwargs.update(
        {
            "docs_url": None,
            "redoc_url": None,
            "root_path": "/api/tutor",
        },
    )

app = FastAPI(**common_kwargs)

active_connections: dict[str, WebSocket] = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        - 在 refactor branch 中, 這段程式碼與 `src.main.swagger_ui_redirect` 已被整合並移至單一模組 `app.api.docs` 中. - 至於為什麼最上層模組名稱是 `app` 而不是 `src`, 請參考 `src` 的說明.

    
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

    *由 林家民 於 2025/7/25 撰寫, 原文為自己寫的英文, 由 ChatGPT 翻譯為繁體中文. *
    """
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(announcement_router)
app.include_router(ws_router)


async def determine_role(card_id: str) -> Cardholder:
    """根據卡片號碼判斷該持卡人是學生還是老師.

    Parameters
    ----------
    card_id : str
        就是卡片 ID, 還能是什麼?

    Returns
    -------
    Cardholder
        請見 `src.models.cardholder`

    .. todo::
        此函式不應該放在 `src.main`, 應移至獨立的 service class.
    """
    cardholder = Cardholder(**await exec_sql("one", "fetch_role_student", card_id=card_id))

    if isinstance(cardholder.name, str):
        cardholder.role = "student"
        logger.info("Cardholder is student: %s", cardholder.model_dump_json(indent=2))

    elif cardholder.name is None:
        logger.info("Cardholder is not a student, trying teacher")
        cardholder = Cardholder(**await exec_sql("one", "fetch_role_teacher", card_id=card_id))

        if cardholder.name is None:
            logger.error("Error: Can't find info for %s", card_id)
            return "刷卡失敗: 查無此人"

        if isinstance(cardholder.name, str):
            cardholder.role = "teacher"
            associated_device = await exec_sql(
                "one",
                "fetch_associated_device",
                teacher_id=cardholder.card_id,
            )
            if associated_device != {}:
                cardholder.device_id = associated_device["設備號碼"]
            logger.info("Cardholder is teacher: %s", cardholder.model_dump_json(indent=2))

    cardholder.card_id = (
        cardholder.card_id.strip() if cardholder.card_id is not None else cardholder.card_id
    )
    return cardholder


@app.post("/update")
async def update_teacher_info(cardholder: Cardholder) -> dict:
    """更新教師的大學.

    Parameters
    ----------
    cardholder : Cardholder
        見 `src.models.cardholder`

    Returns
    -------
    dict
        就 "detail": "Update success".

    .. todo::
        應重構為獨立的 service class。
    """
    await exec_sql(
        "commit",
        "update_teacher_info",
        card_id=cardholder.card_id,
        college=cardholder.school,
    )
    await sync_frontend()

    return {
        "detail": "Update success",
    }


def handle_device_zero(cardholder: Cardholder) -> Cardholder | None:
    """回傳給  的資料.

    雖然裝置 ID 1-6 對應實體的讀卡設備,  呼叫該 endpoint 時會使用裝置 ID 為 0, 而本函式即處理該情境下的 cardholder 物件.

    Parameters
    ----------
    cardholder : Cardholder
        請見 `src.models.cardholder`

    Returns
    -------
    Cardholder | None
        若為教師則回傳 cardholder, 否則不回傳任何內容 (因為僅允許教師透過前端編輯資料)

    Raises
    ------
    HTTPException
        若該 ID 不屬於教師, 則拋出錯誤.

    .. todo::
        應重構為獨立的 service class。
    """  # noqa: E501
    if cardholder.role == "teacher":
        return cardholder
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found for device 0")



@app.get(
    "/{device_id}/{card_id}",
    responses={
        200: {
            "description": "XXX老師 刷卡成功 | XXX學生 刷卡成功 | 刷卡失敗: XXX",
        },
    },
)
async def register_card_id(device_id: int, card_id: str) -> Cardholder | str | None:
    """註冊學生與老師的卡片 ID.

    此函式會先判斷該卡片 ID 是否有效, 並確認是屬於學生或老師.

    若為學生卡, 系統會檢查該設備是否已有老師打卡(也就是老師在學生刷卡前就已經刷過).若沒有, 則拒絕此次刷卡.

    若老師已事先刷卡, 接著判斷該學生當日刷卡次數.若為第一次, 表示進入諮詢時段; 若為第二次, 則表示結束諮詢.

    反之, 若為老師卡, 會先判斷目前刷卡的設備是否與前一次相同.也就是說, 若該老師之前在裝置 1 刷卡, 現在又在裝置 2 刷卡, 系統需先將其從裝置 1 註銷, 再加入裝置 2.

    最後, 若老師再次於相同設備刷卡, 則表示該老師正在簽退.

    Parameters
    ----------
    device_id : int
        範圍為 0-6, 1-6 對應實體的樹莓派設備, 0 表示來自前端的請求.
    card_id : str
        應有更嚴格的驗證規則, 雖然傳入 SQL 前已有 SQLAlchemy 的保護機制.

    Returns
    -------
    Cardholder | str | None
        若是前端呼叫, 將回傳該卡持有者的資料; 若是實體裝置呼叫, 則回傳要顯示於 Pi 裝置上的文字.

    .. todo::
        應重構為獨立的 service class。

    
    """  # noqa: E501
    try:
        cardholder = await determine_role(card_id=card_id)
        if device_id == 0:
            return handle_device_zero(cardholder=cardholder)


        if cardholder.role == "teacher":
            if cardholder.device_id == device_id:
                logger.info(
                    "Cardholder device_id matches incoming device_id",
                )
                await exec_sql(
                    "commit",
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=device_id,
                )
                logger.info("Clearing device and return early")
                await sync_frontend()
                return f"{cardholder.name}老師 刷卡成功"

            if cardholder.device_id is not None and cardholder.device_id != device_id:
                logger.info(
                    "Cardholder has a device assigned and it's not this device, will clear DB",
                )
                await exec_sql(
                    "commit",
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=cardholder.device_id,
                )
            logger.info("Assigning this device to the teacher and returning early.")
            await exec_sql(
                "commit",
                "register_update_teacher",
                teacher_id=cardholder.card_id,
                device_id=device_id,
            )
            await sync_frontend()
            return f"{cardholder.name}老師 刷卡成功"

        if cardholder.role == "student":
            device = Device(
                device_id=device_id,
                teacher_id=(await exec_sql("one", "check_for_teacher", device_id=str(device_id)))[
                    "老師編號"
                ],
            )
            logger.info("Device info: %s", device.model_dump_json(indent=2))
            if device.teacher_id is None:
                logger.info("Device has no teacher, returning error")
                return "刷卡失敗: 輔導老師未刷卡"

            reservation_id = await exec_sql(
                "one",
                "register_select",
                student_id=cardholder.card_id,
                teacher_id=device.teacher_id,
            )
            if reservation_id == {}:
                logger.info("Student has no reservation ID associated, proceeding to create one")
                await exec_sql(
                    "commit",
                    "register_insert",
                    student_id=cardholder.card_id,
                    teacher_id=device.teacher_id,
                )
            else:
                logger.info(
                    "Student has reservation ID, proceeding to update time for end of class",
                )
                await exec_sql(
                    "commit",
                    "register_update_student",
                    reservation_id=reservation_id["自動編號"],
                )
            await sync_frontend()
            return f"{cardholder.name}學生 刷卡成功"
    except Exception:
        logger.exception("Unexpected error")
        return "刷卡失敗: API 錯誤"
