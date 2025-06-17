from rich.logging import RichHandler
from rich.traceback import install
import logging
from pathlib import Path as pathlib_Path
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, status
import tomllib
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from src.database.exec_sql import async_engine
from src.schemas import SMSModel, ErrorResponse
from src.handle_sms import handle_sms
from src.decode_big5 import decode_big5
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

install(show_locals=True)
rich_handler = RichHandler(rich_tracebacks=True)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[rich_handler]
)
for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    logger = logging.getLogger(name)
    logger.handlers = [rich_handler]
    logger.setLevel(logging.INFO)

logger = logging.getLogger("rich")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if async_engine:
        await async_engine.dispose()

current_file = pathlib_Path(__file__).resolve()
backend_pyproject_path = current_file.parent.parent / "pyproject.toml"
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)
title = backend_data.get("project", {}).get("name", " FastAPI Project")
version = backend_data.get("project", {}).get("version", "0.0.0")
description = backend_data.get("project", {}).get("description", "description here")


app = FastAPI(
    title=title,
    description=description,
    version=version,
    docs_url=None,
    redoc_url=None,
    root_path="/api/sms",
    lifespan=lifespan,
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

@app.get("/sms",
         response_class=HTMLResponse,
         response_description="回傳 'Success' HTML",
         tags=["簡訊系統"],
         summary="發送簡訊",
         description="",
         responses={
        200: {
            "content": {
                "text/html": {
                    "example": """
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success</title>
</head>
<body>
    <h1>Success</h1>
</body>
</html>
"""
                }
            },
            "description": "HTML 格式的成功頁面"
        },
        404: {
            "model": ErrorResponse,
            "description": "格式錯誤或其他例外"
        }
    }
         )
async def get_send_sms(
    background_tasks: BackgroundTasks,
    student_id: str = Query(..., description="學生學號"),
    recipient: str = Query(..., description="收件人姓名"),
    phone_number: str = Query(..., description="手機號碼"),
    message_content: str = Query(..., description="簡訊內容"),
    send_time: str | None = Query(None, description="預約發送時間")
) -> str:

    try:
        sms_request: SMSModel = SMSModel(
            student_id=student_id,
            recipient=decode_big5(recipient),
            phone_number=phone_number,
            message_content=decode_big5(message_content),
            send_time=send_time)
        logging.info(f'[SUCCESS] Received request: {sms_request.model_dump}')

    except Exception as e:
        logging.error(f'[ERROR] {e}')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="格式錯誤或其他例外"
        )

    background_tasks.add_task(handle_sms, sms_request)

    return """
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success</title>
</head>
<body>
    <h1>Success</h1>
</body>
</html>
"""
