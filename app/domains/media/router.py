
import logging
import os

from fastapi import APIRouter

from app.domains.media.routers import video, picture
from os import getenv
# Static variables
# TODO move them to .env
SMB_URL = f"//{getenv('SMB_HOST', '')}{getenv('SMB_FOLDER', '')}"
SMB_USERNAME = getenv("SMB_USERNAME", "")
SMB_PASSWORD = getenv("SMB_PASSWORD", "")
CHUNK_SIZE = 512 * 1024  # 512 KB
STATIC_FOLDER = "./static"
video_cycler = None
# Configure logging
logger = logging.getLogger("__name__")

router = APIRouter(prefix="/media")


def get_local_filenames() -> list[str]:
    return [
        filename for filename in os.listdir(STATIC_FOLDER) if filename.endswith(".mp4")
    ]


router.include_router(video.router)
router.include_router(picture.router)