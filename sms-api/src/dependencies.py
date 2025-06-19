from src.models import SMSModel
import logging
from pprint import pformat
from urllib.parse import unquote
import chardet
from src.config import settings
import logging

logger = logging.getLogger("rich")


def return_url_list(data: SMSModel):
    url_list = {
        "1": f"",
        "2": f"",
        "3": f"",
    }
    logger.info(pformat(url_list, indent=2))
    return url_list


def decode_big5(message):
    try:
        decoded_url = unquote(message).encode()
        if decoded_url:

            encoding = chardet.detect(decoded_url)["encoding"]
            logger.info(f"Encoding is {encoding}")
            if encoding:
                result = decoded_url.decode(encoding=encoding)
            else:
                logger.error("encoding is False or undefined")
        else:
            logger.error("decoded_url is False or undefined")
            raise ValueError
    except Exception as e:
        logger.exception("Exception occured!")

    logger.info(f"Decoding success! Message: {result}")
    return result
