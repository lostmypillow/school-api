import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from src.database.exec_sql import async_engine
from src.schemas import SMSModel, ErrorResponse
from src.handle_sms import handle_sms
from src.decode_big5 import decode_big5


async def lifespan(app: FastAPI):
    """Disposes SQLAlchemy engine
    """
    yield
    if async_engine:
        await async_engine.dispose()

# Entry of the FastAPI app
app = FastAPI(
    title="SMS 簡訊推播系統",
    description="簡訊發送與推播後端 API",
    version="0.2.0",
    lifespan=lifespan,
)


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
