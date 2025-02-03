from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from database.async_operations import exec_sql, async_engine
from lib.sms_model import SMSModel
from lib.handleSMS import handleSMS
from lib.decode_big5 import decode_big5
import markdown
from pathlib import Path
from lib.custom_logger import logger
load_dotenv()


async def lifespan(app: FastAPI):
    """Disposes SQLAlchemy engine
    """
    yield
    if async_engine:
        await async_engine.dispose()

# Entry of the FastAPI app
app = FastAPI(
    lifespan=lifespan,

    title="簡訊&推播系統 / SMS",

    version="0.1.1"
)

@app.get("/", response_class=HTMLResponse)
async def read_readme():
    # Path to the README.md file
    readme_path = Path(__file__).parent / "README.md"
    
    # Read the README.md file
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(readme_content)
    
    # Return the HTML response
    return html_content


@app.get("/sms", response_class=HTMLResponse)
async def get_send_sms(
    background_tasks: BackgroundTasks,
    student_id: str,
    recipient: str,
    phone_number: str,
    message_content: str,
    send_time: str = None
) -> str:
    """給 VB app 的 Endpoint

    Parameters
    ----------
    background_tasks : BackgroundTasks
        FastAPI 內建功能

    student_id : str
        學號

    recipient : str
        對象

    phone_number : str
        手機號碼

    message_content : str
        簡訊內容

    send_time : str, optional
        預約時間, by default None

    Returns
    -------
    str
        "sent"

    Raises
    ------
    HTTPException
        'Format Error'
    """

    try:
        sms_request: SMSModel = SMSModel(
            student_id=student_id,
            recipient=decode_big5(recipient),
            phone_number=phone_number,
            message_content=decode_big5(message_content),
            send_time=send_time)

    except Exception as e:
        logger.error(f'[ERROR] {e}')
        raise HTTPException(404, 'Format Error')

    background_tasks.add_task(handleSMS, sms_request)

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
