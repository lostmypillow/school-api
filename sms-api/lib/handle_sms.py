from lib.database.async_operations import exec_sql
import random
import xml.etree.ElementTree as ET
from lib.sms_model import SMSModel
from httpx import Response, AsyncClient
from bs4 import BeautifulSoup
import urllib.parse
from lib.custom_logger import logger
from config import settings

async def handle_sms(data: SMSModel):
    # todo http > 1-2
    url_list: dict = {

        "1": ,

        "2": f"",

        "3": 

    }

    try:

        # Check if phone number is associated with a preferred vendor
        preferred_vendor = await exec_sql(
            "one",
            "get_specified_vendor",
            phone_number=data.phone_number)
        logger.info(f'[HANDLE SMS] Preferred vendor: {preferred_vendor}')
    except Exception as e:
        logger.info(f'[HANDLE SMS] Error getting preferred vendor: {e}')

    # If phone number has preferred vendor, use preferred vendor
    if preferred_vendor is not None:
        vendor_id = str(preferred_vendor['限定廠商編號'])
        logger.info(
            f'[HANDLE SMS] Phone num has preferred vendor, vendor chosen: {vendor_id}')

    # If message content has http, randomize vendor 1 and 2
    elif data.message_content.find('http') != -1:
        vendor_id = str(random.randint(1, 2))
        logger.info(
            f'[HANDLE SMS] Content has http, vendor chosen: {vendor_id}')

        # If none of the above, randomize 1 to 3
    else:
        vendor_id = str(random.randint(1, 3))
        logger.info(f'[HANDLE SMS] Vendor chosen: {vendor_id}')

    # If it is vendor 1 and 2...
    if vendor_id != "3":

        # ...and if length of message exceeds 7 characters...
        if len(data.message_content) >= 7:

            # ...append longsms to url
            url_list[vendor_id] += "&longsms=Y"

            # ...and if send_time is specified...
        if data.send_time is not None:

            # append send time to url
            url_list[vendor_id] += f"&sendtime={data.send_time}"

    logger.info(f'[HANDLE SMS] Vendor URL constructed: {url_list[vendor_id]}')

    # With httpx's AsyncClient
    async with AsyncClient() as client:

        # Gets response from sms vendor
        try:
            response: Response = await client.get(url_list[vendor_id])
            soup = BeautifulSoup(response.text, 'html.parser')
            sms_id = soup.find(
                'msgid').text if vendor_id != "3" else soup.find('msg').text
            logger.info(
                f'[HANDLE SMS] Got response from vendor. ID is {sms_id}')
        except Exception as e:
            logger.info(f'[HANDLE SMS] Error response from vendor: {e}')

        try:
            logger.info(f'[HANDLE SMS] FCM URL: https://"+ {settings.notif_api} +".')
            await client.post(
                "https://"+ settings.notif_api +".", data={
                    "student_id": data.student_id,
                    "title": "簡訊通知",
                    "body": data.message_content
                }, headers={"Content-Type": "application/json"})

        except Exception as e:
            logger.info(f'[HANDLE SMS] Error response from app notif: {e}')

    try:
        await exec_sql(
            "commit",
            "insert_record",
            student_id=data.student_id,
            recipient=data.recipient,
            phone_number=data.phone_number,
            sms_id=sms_id,
            message_content=data.message_content,
            vendor_id=vendor_id
        )
        logger.info(f'[HANDLE SMS] Inserted into db ')
    except Exception as e:
        logger.info(f'[HANDLE SMS] Error inserting into db: {e}')
