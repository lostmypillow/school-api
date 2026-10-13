from fastapi import APIRouter, Depends, BackgroundTasks
from src.dependencies import SMBSession, get_smb_session
from fastapi.exceptions import HTTPException
from fastapi.responses import PlainTextResponse
import smbclient
import logging
import shutil
from src.config import settings
logger = logging.getLogger("__name__")
import os
video_cycler = None
router = APIRouter(
    prefix="/video",
    tags=["Videos"],
)
STATIC_FOLDER = "/srv/dl_videos"
SMB_URL = f"//{settings.SMB_HOST}{settings.SMB_FOLDER}"

from itertools import cycle

@router.post("/sync")
def sync_videos_from_smb_2_local(smb: SMBSession = Depends(get_smb_session)):

    def dl_vid(file):
        with smbclient.open_file(
                            os.path.join(SMB_URL, file.name), mode="rb"
                        ) as smb_file:
                            with open(local_file_path, "wb") as local_file:
                                shutil.copyfileobj(smb_file, local_file)

    global video_cycler
    with smb:
        try:
            for file in smbclient.scandir(SMB_URL):
                
    
                if file.name.endswith(".mp4"):
                    
                    local_file_path = os.path.join(STATIC_FOLDER, file.name)
                    logger.info(local_file_path)
                    if not os.path.exists(local_file_path):
                        logger.info(f"Downloading {file.name} from SMB")
                        dl_vid(file=file)
                        logger.info(f"Downloaded {file.name}")
                    else:
                        logger.info(f"{file.name} exists. Skipping.")
        except Exception as e:
            logger.exception(f"Error syncing files from SMB")
        finally:
            video_cycler = cycle(
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
# # """Upload video to SMB and sync to local static folder."""


# @router.post(
#     "/upload",
    
# )
# async def upload_video(file: UploadFile = File(...)):
#     file_path = os.path.join(SMB_URL, file.filename)

#     with smb:
#         try:
#             with smbclient.open_file(file_path, mode='wb') as smb_file:
#                 while chunk := await file.read(CHUNK_SIZE):
#                     smb_file.write(chunk)

#             local_file_path = os.path.join(STATIC_FOLDER, file.filename)
#             with smbclient.open_file(file_path, mode='rb') as smb_file:
#                 with open(local_file_path, 'wb') as local_file:
#                     shutil.copyfileobj(smb_file, local_file)

#             logging.info(f"Uploaded {file.filename} and synced to static folder.")
#             return {"message": f"File '{file.filename}' uploaded successfully"}
#         except Exception as e:
#             logging.error(f"Upload failed: {e}")
#             raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


# #     """Delete video from SMB and local static folder."""
# @router.delete("/video/{file_name}")
# async def delete_video(file_name: str):
#     smb_file_path = os.path.join(SMB_URL, file_name)

#     with smb:
#         try:
#             if smbclient.path.exists(smb_file_path):
#                 smbclient.remove(smb_file_path)
#                 logging.info(f"Deleted {file_name} from SMB")

#             local_file_path = os.path.join(STATIC_FOLDER, file_name)
#             if os.path.exists(local_file_path):
#                 os.remove(local_file_path)
#                 logging.info(f"Deleted {file_name} from local storage")

#             return {"message": f"File '{file_name}' deleted successfully"}
#         except Exception as e:
#             logging.error(f"Error deleting file {file_name}: {e}")
#             raise HTTPException(status_code=500, detail=f"Delete failed: {e}")
