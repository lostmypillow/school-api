from fastapi import FastAPI, BackgroundTasks
import asyncio
import httpx
from httpx import Response
import random
from database.async_operations import fetch_one_sql, commit_sql
from pydantic import BaseModel
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


class SMSRequest(BaseModel):

    # 學號
    student_id: str

    # 對象
    recipient: str

    # 手機
    phone_number: str

    # 內容
    message_content: str


async def handleSMS(data: SMSRequest):
    url_list = {
        "1":  + str(data.phone_number) +  + str(data.message_content) + ,
        "2":  + str(data.phone_number) +  + str(data.message_content) + ,
        "3":  + str(data.phone_number) +  + str(data.message_content)
    }
    preferred_vendor = await fetch_one_sql("get_specified_vendor", phone_number=data.phone_number)
    vendor_id = random.randint(
        1, 3) if preferred_vendor is None else preferred_vendor.限定廠商編號

    async with httpx.AsyncClient() as client:
        response: Response = await client.post(url_list[str(vendor_id)])
        sms_id = ET.fromstring(response.text).find("msgid").text
    await commit_sql(
        "insert_record",
        student_id=data.student_id,
        recipient=data.recipient,
        phone_number=data.phone_number,
        sms_id=sms_id,
        message_content=data.message_content,
        vendor_id=vendor_id
    )


@app.post("/sms")
async def send_sms(sms_request: SMSRequest, background_tasks: BackgroundTasks) -> str:
    background_tasks.add_task(handleSMS, sms_request)
    return "sent"
