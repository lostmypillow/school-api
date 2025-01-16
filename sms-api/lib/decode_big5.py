from urllib.parse import unquote
import chardet


def decode_big5(message):
    print(f"Decoding: {message}")
    decoded_url = unquote(message)
    return decoded_url.encode().decode(
        chardet.detect(decoded_url.encode())['encoding'])
