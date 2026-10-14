import logging

import smbclient
from fastapi import HTTPException
from starlette import status

logger = logging.getLogger(__name__)


class SMBSession:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password

    def __enter__(self):
        try:
            smbclient.register_session(
                server=self.host, username=self.username, password=self.password
            )
            return self
        except Exception:
            logger.exception("Error opening SMB session")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect to SMB server.",
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            smbclient.reset_connection_cache()
        except Exception as e:
            logging.error(f"Error closing SMB session: {e}")
