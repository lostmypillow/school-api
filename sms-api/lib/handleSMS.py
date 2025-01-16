from database.async_operations import fetch_one_sql, commit_sql
import random
import xml.etree.ElementTree as ET
from .sms_model import SMSModel
from httpx import Response, AsyncClient





async def handleSMS(data: SMSModel):
    url_list: dict = {

        "1": ,

        "2": f"",

        "3": 

    }

    try:
        preferred_vendor = await fetch_one_sql("get_specified_vendor", phone_number=data.phone_number)
        vendor_id = str(random.randint(
            1, 3) if preferred_vendor is None else preferred_vendor.限定廠商編號)
        if vendor_id != "3":
            if len(data.message_content) >= 7:
                url_list[vendor_id] += "&longsms=Y"
            if data.send_time is not None:
                url_list[vendor_id] += f"&sendtime={data.send_time}"

        print(url_list[vendor_id])


        async with AsyncClient() as client:
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