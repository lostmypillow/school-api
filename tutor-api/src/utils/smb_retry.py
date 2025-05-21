import smbclient
from smbprotocol.exceptions import UserSessionDeleted
from src.config import settings
import functools
import logging

logger = logging.getLogger("uvicorn.error")

def smb_retry(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UserSessionDeleted:
            logger.warning("Caught UserSessionDeleted — refreshing SMB session and retrying.")
            smbclient.reset_connection_cache()
            smbclient.register_session(
                server=settings.SMB_HOST,
                username=settings.SMB_USERNAME,
                password=settings.SMB_PASSWORD
            )
            return await func(*args, **kwargs)
    return wrapper
