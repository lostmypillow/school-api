from fastapi.middleware.cors import CORSMiddleware
from pprint import pformat
from .routers import sync_frontend, ws_router, announcement_router
import traceback
from src.config import settings
from .models import Cardholder, Device
from src.database.exec_sql import async_engine, exec_sql
from fastapi.exceptions import HTTPException
from fastapi import FastAPI, WebSocket
import tomllib
from contextlib import asynccontextmanager
from rich import print

import os
from typing import cast
from pathlib import Path as pathlib_Path
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from rich.logging import RichHandler
from rich.traceback import install
import logging

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

logger = logging.getLogger("rich")
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
            "root_path": "/api/tutor",
        }
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
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.root_path + cast(str, app.openapi_url),
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/assets/swagger-ui-bundle.js",
        swagger_css_url="/assets/swagger-ui.css",
        swagger_favicon_url="/assets/favicon.ico",
    )


@app.get(cast(str, app.swagger_ui_oauth2_redirect_url), include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


app.include_router(announcement_router)
app.include_router(ws_router)


@app.post("/update")
async def update_teacher_info(cardholder: Cardholder):
    try:
        await exec_sql(
            "commit",
            "update_teacher_info",
            card_id=cardholder.card_id,
            college=cardholder.school,
        )
        await sync_frontend()
    except Exception as e:
        return HTTPException(404)


@app.get(
    "/{device_id}/{card_id}",
    responses={
        200: {
            "description": "XXX老師 刷卡成功 | XXX學生 刷卡成功 | 刷卡失敗: XXX",
        }
    },
)
async def register_card_id(device_id: int, card_id: str):
    try:
        cardholder = Cardholder(
            **await exec_sql("one", "fetch_role_student", card_id=card_id)
        )

        if type(cardholder.name) == str:
            cardholder.role = "student"
            logger.info(f"Cardholder is student: {pformat(cardholder.model_dump())}")
            if device_id == 0:
                raise HTTPException(404, "Not eligible")

        elif cardholder.name == None:
            print("Cardholder is not a student, trying teacher")
            cardholder = Cardholder(
                **await exec_sql("one", "fetch_role_teacher", card_id=card_id)
            )

            if cardholder.name == None:
                logger.error(f"Error: Can't find info for {card_id}")
                return "刷卡失敗: 查無此人"

            elif type(cardholder.name) == str:
                cardholder.role = "teacher"
                associated_device = await exec_sql(
                    "one", "fetch_associated_device", teacher_id=cardholder.card_id
                )
                if associated_device != {}:
                    cardholder.device_id = associated_device["設備號碼"]
                logger.info(
                    f"Cardholder is teacher: {pformat(cardholder.model_dump())}"
                )

        cardholder.card_id = (
            cardholder.card_id.strip()
            if cardholder.card_id is not None
            else cardholder.card_id
        )

        if cardholder.role == "teacher":
            if device_id == 0:
                return cardholder
            if cardholder.device_id == device_id:
                logger.info(
                    "Cardholder device_id matches incoming device_id, will clear this device and return early"
                )
                await exec_sql(
                    "commit",
                    "register_update_teacher",
                    teacher_id=None,
                    device_id=device_id,
                )
                await sync_frontend()
                return f"{cardholder.name}老師 刷卡成功"

            elif cardholder.device_id is not None and cardholder.device_id != device_id:
                logger.info(
                    "Cardholder has a device assigned and it's not this device, will clear DB"
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

        elif cardholder.role == "student":
            device = Device(
                device_id=device_id,
                teacher_id=(
                    await exec_sql("one", "check_for_teacher", device_id=str(device_id))
                )["老師編號"],
            )
            logger.info(f"Device info: {pformat(device.model_dump())}")
            if device.teacher_id == None:
                logger.info("Device has no teacher, returning error")
                return "刷卡失敗: 輔導老師未刷卡"

            reservation_id = await exec_sql(
                "one",
                "register_select",
                student_id=cardholder.card_id,
                teacher_id=device.teacher_id,
            )
            if reservation_id == {}:
                logger.info(
                    "Student has no reservation ID associated, proceeding to create one"
                )
                await exec_sql(
                    "commit",
                    "register_insert",
                    student_id=cardholder.card_id,
                    teacher_id=device.teacher_id,
                )
            else:
                logger.info(
                    "Student has reservation ID, proceeding to update time for end of class"
                )
                await exec_sql(
                    "commit",
                    "register_update_student",
                    reservation_id=reservation_id["自動編號"],
                )
            await sync_frontend()
            return f"{cardholder.name}學生 刷卡成功"
    except Exception as e:
        logger.exception(f"[main] Unexpected error:\n{traceback.format_exc()}")
        return "刷卡失敗: API 錯誤"
