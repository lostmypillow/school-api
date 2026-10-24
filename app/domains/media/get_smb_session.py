from os import getenv

from app.domains.media.smb_session import SMBSession


def get_smb_session() -> SMBSession:
    return SMBSession(
        host=getenv('SMB_HOST', ''),
        username=getenv('SMB_USERNAME', ''),
        password=getenv('SMB_PASSWORD', ''),
    )
