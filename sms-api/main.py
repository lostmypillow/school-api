from fastapi import FastAPI, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from database.async_session import async_engine
from lib.sms_model import SMSModel
from lib.handleSMS import handleSMS
from lib.decode_big5 import decode_big5
load_dotenv()


async def lifespan(app: FastAPI):
    """Generator for FastAPI lifespan management
    """
    yield
    await async_engine.dispose()

app = FastAPI(lifespan=lifespan)


@app.post("/sms")
async def send_sms(
    sms_request: SMSModel,
    background_tasks: BackgroundTasks
) -> str:

    background_tasks.add_task(handleSMS, sms_request)

    return "sent"


@app.get("/sms")
async def get_send_sms(
    background_tasks: BackgroundTasks,
    student_id: str,
    recipient: str,
    phone_number: str,
    message_content: str,
    send_time: str =None
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
        print(e)
        raise HTTPException(404, 'Format Error')

    background_tasks.add_task(handleSMS, sms_request)

    return "sent"
