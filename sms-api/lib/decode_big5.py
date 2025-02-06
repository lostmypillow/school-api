from urllib.parse import unquote
import chardet
from lib.custom_logger import logger


def decode_big5(message):
    decoded_url = unquote(message).encode()
    result = decoded_url.decode(chardet.detect(decoded_url)['encoding'])
    logger.info(f"[DECODED] Message: {result}")
    return result
