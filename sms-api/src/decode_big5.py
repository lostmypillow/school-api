import logging
from urllib.parse import unquote
import chardet


def decode_big5(message):
    decoded_url = unquote(message).encode()
    result = decoded_url.decode(chardet.detect(decoded_url)['encoding'])
    logging.info(f"[DECODED] Message: {result}")
    return result
