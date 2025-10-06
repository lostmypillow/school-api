import logging
import random
from httpx import Response, AsyncClient, Timeout
from bs4 import BeautifulSoup
from src.models import SMSModel
from src.database.exec_sql import exec_sql
from src.config import settings
from src.dependencies import return_url_list
from pprint import pformat
logger = logging.getLogger("rich")


async def handle_sms(data: SMSModel):
    url_list = return_url_list(data=data)
    vendor_id = None

    try:

        # Check if phone number is associated with a preferred vendor
        preferred_vendor = await exec_sql(
            "one", "get_specified_vendor", phone_number=data.phone_number
        )
    except Exception as e:
        logger.exception(f"Error getting preferred vendor:\n{data.model_dump_json(indent=2)}")

    # If phone number has preferred vendor, use preferred vendor
    if preferred_vendor is not None:
        vendor_id = preferred_vendor.get("限定廠商編號")
        if vendor_id is None or str(vendor_id) == "0":
            logger.warning(
                f"preferred_vendor missing key '限定廠商編號': {preferred_vendor}"
            )
            vendor_id = None
        else:
            vendor_id = str(vendor_id)
        logger.info(f"Phone number {data.phone_number} will go through vendor No. {vendor_id}")

    # If message content has http, randomize vendor 1 and 2
    if vendor_id is None and data.message_content.find("http") != -1:
        vendor_id = str(random.randint(1, 2))
        logger.info(
            f"{data.phone_number} has http in message content, choosing vendor {vendor_id}"
        )

        # If none of the above, randomize 1 to 3
    if vendor_id is None:
        vendor_id = str(random.randint(1, 2))
        logger.info(f"{data.phone_number} has no preferred vendor or 'http' in message, choosing: {vendor_id}")

    # If it is vendor 1 and 2...
    if vendor_id != "3":

        # ...and if length of message exceeds 7 characters...
        if len(data.message_content) >= 7:

            logger.info(
                f"{data.phone_number} has message that exceeds 7 characters, appending longsms fragment"
            )

            # ...append longsms to url
            url_list[vendor_id] += "&longsms=Y"

            # ...and if send_time is specified...
        if data.send_time is not None:

            logger.info(
                f"{data.phone_number} sendtime is specified, adding sendtime fragment"
            )

            # append send time to url
            url_list[vendor_id] += f"&sendtime={data.send_time}"

    if vendor_id not in url_list:
        vendor_id = "2"

    logger.info(
        f"Vendor URL constructed: {url_list[vendor_id]} for {data.phone_number}"
    )
    sms_id = "N/A"
    # With httpx's AsyncClient
    async with AsyncClient(timeout=Timeout(10.0, connect=5.0)) as client:

        # Gets response from sms vendor
        try:
            response: Response = await client.get(url_list[vendor_id])
            soup = BeautifulSoup(response.text, "html.parser")
            tag = soup.find("msgid") if vendor_id != "3" else soup.find("msg")
            logger.info(response.text)
            sms_id = tag.text if tag else "NOT_FOUND"
            logger.info(f"Got response from vendor. ID is {sms_id}")
        except Exception as e:
            logger.exception(f"Error response from vendor: {e}")

        try:
            logger.info(
                f"FCM URL: "
            )
            res_data = {
                "student_id": data.student_id,
                "phone": data.phone_number,
                "title": "簡訊通知",
                "body": data.message_content,
            }
            res = await client.post(
                "https://"
                + settings.notif_api
                + ".",
                data=res_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            logger.info(f"Res_data variable: {res_data}")
            logger.info(pformat(res_data,indent=2))

        except Exception as e:
            logger.exception(f"Error response from app notif API: {e}")

    try:
        await exec_sql(
            "commit",
            "insert_record",
            student_id=data.student_id,
            recipient=data.recipient,
            phone_number=data.phone_number,
            sms_id=sms_id,
            message_content=data.message_content,
            vendor_id=vendor_id,
        )
        logger.info(f"Inserted into db!")
    except Exception as e:
        logger.exception(f"Error inserting into db: {e}")
