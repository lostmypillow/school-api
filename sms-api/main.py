from fastapi import FastAPI, BackgroundTasks, HTTPException
import asyncio
from typing import Any
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

    # 預約時間
    send_time: Any


async def handleSMS(data: SMSRequest):
    url_list: dict = {
        "1":  + str(data.phone_number) +  + str(data.message_content) +  + "&longsms=Y" if len(data.message_content) >= 70 else "" + f"&sendtime = {data.send_time}" if data.send_time is not None else "",
        "2":  + str(data.phone_number) +  + str(data.message_content) +  "&longsms=Y" if len(data.message_content) >= 70 else "" + f"&sendtime = {data.send_time}" if data.send_time is not None else "",
        "3":  + str(data.phone_number) +  + str(data.message_content)
    }
    preferred_vendor = await fetch_one_sql("get_specified_vendor", phone_number=data.phone_number)
    vendor_id = str(random.randint(
        1, 3) if preferred_vendor is None else preferred_vendor.限定廠商編號)

    try:
        async with httpx.AsyncClient() as client:
            response: Response = await client.post(url_list[vendor_id])
            sms_id = ET.fromstring(response.text).find("msgid").text

            await client.post("https://studev.", {
                "student_id": data.student_id,
                "phone": data.phone_number,
                "title": "簡訊通知",
                "body": data.message_content
            })
        await commit_sql(
            "insert_record",
            student_id=data.student_id,
            recipient=data.recipient,
            phone_number=data.phone_number,
            sms_id=sms_id,
            message_content=data.message_content,
            vendor_id=vendor_id
        )

    except Exception as e:
        print(e)


@app.post("/sms")
async def send_sms(sms_request: SMSRequest, background_tasks: BackgroundTasks) -> str:
    background_tasks.add_task(handleSMS, sms_request)
    return "sent"


@app.get("/sms")
async def get_send_sms(background_tasks: BackgroundTasks, student_id: str, recipient: str, phone_number: str, message_content: str, send_time = None) -> str:
    try:
        sms_request: SMSRequest = SMSRequest(
        student_id=student_id,
        recipient=recipient,
        phone_number=phone_number,
        message_content=message_content,
        send_time=send_time)

    except Exception as e:
        print(e)
        raise HTTPException(404, 'Format Error')
    
    background_tasks.add_task(handleSMS, sms_request)
    return "sent"
