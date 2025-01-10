from fastapi import FastAPI, BackgroundTasks
import asyncio
import httpx
import random
from database.async_operations import fetch_one_sql, commit_sql
from pydantic import BaseModel
app = FastAPI()


class SMSRequest(BaseModel):
    student_id: str
    recipient: str
    phone_number: str
    message_content: str


async def handleSMS(data: SMSRequest):
    # sms_id = 0
    # sms_id = 262227520
    url_list = {
        "1":  + str(data.phone_number) +  + str(data.message_content) + ,
        "2":  + str(data.phone_number) +  + str(data.message_content) + ,
        "3":  + str(data.phone_number) +  + str(data.message_content)
    }
    preferred_vendor = await fetch_one_sql("get_specified_vendor", phone_number=data.phone_number)
    vendor_id = random.randint(
        1, 3) if preferred_vendor is None else preferred_vendor.限定廠商編號

    # async with httpx.AsyncClient() as client:
    #     response = await client.post(url_list[str(vendor_id)])
    #     print(response.status_code)
    #     print(response)
    print(url_list[str(vendor_id)])
    await commit_sql(
        "insert_record",
        student_id=data.student_id,
        recipient=data.recipient,
        phone_number=data.phone_number,
        sms_id=sms_id,
        message_content=data.message_content,
        vendor_id=vendor_id
    )


@app.post("/send_sms")
async def send_sms(sms_request: SMSRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(handleSMS, sms_request)
    return "sent"
