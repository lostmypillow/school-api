
import logging
import random
from httpx import Response, AsyncClient
from bs4 import BeautifulSoup
from src.schemas import SMSModel
from src.database.exec_sql import exec_sql
from src.config import settings


async def handle_sms(data: SMSModel):
    # todo http > 1-2
    url_list: dict = {

        "1": f"",

        "2": f"",

        "3": f""

    }

    try:

        # Check if phone number is associated with a preferred vendor
        preferred_vendor = await exec_sql(
            "one",
            "get_specified_vendor",
            phone_number=data.phone_number)
    except Exception as e:
        logging.info(
            f'[HANDLE SMS] Error getting preferred vendor: {e}, debug info: {data}')

    # If phone number has preferred vendor, use preferred vendor
    if preferred_vendor is not None:
        vendor_id = str(preferred_vendor['限定廠商編號'])
        logging.info(f"{data.phone_number} has preferred vendor: {vendor_id}")

    # If message content has http, randomize vendor 1 and 2
    elif data.message_content.find('http') != -1:
        vendor_id = str(random.randint(1, 2))
        logging.info(f"{data.phone_number} has http in message content, choosing vendor {vendor_id}")

        # If none of the above, randomize 1 to 3
    else:

        # temporarily prevent use of 3rd sms API
        vendor_id = "3"
        logging.info(f"{data.phone_number} goes thru vendor {vendor_id}")

    # If it is vendor 1 and 2...
    if vendor_id != "3":

        # ...and if length of message exceeds 7 characters...
        if len(data.message_content) >= 7:

            logging.info(f"{data.phone_number} has message that exceeds 7 characters, appending longsms fragment")

            # ...append longsms to url
            url_list[vendor_id] += "&longsms=Y"

            # ...and if send_time is specified...
        if data.send_time is not None:

            logging.info(f"{data.phone_number} sendtime is specified, adding sendtime fragment")

            # append send time to url
            url_list[vendor_id] += f"&sendtime={data.send_time}"

    logging.info(f'[HANDLE SMS] Vendor URL constructed: {url_list[vendor_id]} for {data.phone_number}')

    # With httpx's AsyncClient
    async with AsyncClient() as client:

        # Gets response from sms vendor
        try:
            response: Response = await client.get(url_list[vendor_id])
            soup = BeautifulSoup(response.text, 'html.parser')
            sms_id = soup.find(
                'msgid').text if vendor_id != "3" else soup.find('msg').text
            logging.info(
                f'[HANDLE SMS] Got response from vendor. ID is {sms_id}')
        except Exception as e:
            logging.info(f'[HANDLE SMS] Error response from vendor: {e}')

        try:
            logging.info(
                f'[HANDLE SMS] FCM URL: ')
            res_data = {
                "student_id": data.student_id,
                "phone": data.phone_number,
                "title": "簡訊通知",
                "body": data.message_content
            }
            res = await client.post(
                "https://" + settings.notif_api + ".",
                data=res_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'})
            logging.info(f'Res_data variable: {res_data}')
            logging.info(f' [HANDLE SMS] {res.status_code} {res.json()}')

        except Exception as e:
            logging.info(
                f'[HANDLE SMS] Error response from app notif API: {e}')

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
        logging.info(f'[HANDLE SMS] Inserted into db ')
    except Exception as e:
        logging.info(f'[HANDLE SMS] Error inserting into db: {e}')
