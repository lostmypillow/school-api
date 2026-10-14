import logging
import shutil
from os import getenv

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import PlainTextResponse
from smbclient import open_file, scandir

from app.domains.media.get_smb_session import get_smb_session
from app.domains.media.smb_session import SMBSession

logger = logging.getLogger("__name__")
import os
video_cycler = None
router = APIRouter(
    prefix="/video",
    tags=["Videos"],
)
STATIC_FOLDER = "/srv/dl_videos"
SMB_URL = f"//{getenv('SMB_HOST', '')}{getenv('SMB_FOLDER')}"

from itertools import cycle

@router.post("/sync")
def sync_videos_from_smb_2_local(smb: SMBSession = Depends(get_smb_session)):

    def dl_vid(target_file):
        with open_file(
                            os.path.join(SMB_URL, target_file.name), mode="rb"
                        ) as smb_file:
                            with open(local_file_path, "wb") as local_file:
                                shutil.copyfileobj(smb_file, local_file)

    global video_cycler
    with smb:
        try:
            for file in scandir(SMB_URL):
                
    
                if file.name.endswith(".mp4"):
                    
                    local_file_path = os.path.join(STATIC_FOLDER, file.name)
                    logger.info(local_file_path)
                    if not os.path.exists(local_file_path):
                        logger.info(f"Downloading {file.name} from SMB")
                        dl_vid(target_file=file)
                        logger.info(f"Downloaded {file.name}")
                    else:
                        logger.info(f"{file.name} exists. Skipping.")
        except Exception as e:
            logger.exception("Error syncing files from SMB", exc_info=e)
        finally:
            video_cycler = cycle[str](
                [f for f in os.listdir(STATIC_FOLDER) if f.endswith(".mp4")]
            )
    return "Sync complete"


@router.get(
    "/local",
    response_model=list[str],
    responses={
        200: {
            "description": "List of available .mp4 files",
            "content": {"application/json": {"example": ["video1.mp4", "video2.mp4"]}},
        }
    },
)
def get_all_files() -> list[str]:
    """Returns a list of .mp4 filenames from the server's local static folder

    Returns
    -------
    list[str]
        List of .mp4 filenames from the server's local static folder
    """
    return [f for f in os.listdir(STATIC_FOLDER) if f.endswith(".mp4")]


@router.get(
    "/next",
    response_model=str,
    response_class=PlainTextResponse,
   
)
def get_next_file():
    global video_cycler
    files= [f for f in os.listdir(STATIC_FOLDER) if f.endswith(".mp4")]
    if not files:

        raise HTTPException(status_code=404, detail="No files available")

    return next(video_cycler, None)