import os
import smbclient as smb
from fastapi import APIRouter, UploadFile, HTTPException
from pathlib import Path
from itertools import cycle
from time import perf_counter
from src.lib.custom_logger import logger
from src.lib.active_connections import active_connections
from src.lib.custom_logger import logger
from src.config import settings


local_dir = Path(__file__).resolve().parent.parent.parent / "static"

smb_dir = f"\\\\{settings.SMB_HOST}{settings.SMB_FOLDER}"


video_queue: list = []

# This is a function
get_next_vid = None


def list_local():
    return [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]


def create_cycler(iterable: list):
    cycler: cycle = cycle(iterable)

    def next_video() -> str:
        return next(cycler, None)
    return next_video


async def sync():
    global active_connections
    global video_queue
    global get_next_vid
    start = perf_counter()
    smb_session = smb.register_session(
        settings.SMB_HOST, username=settings.SMB_USERNAME, password=settings.SMB_PASSWORD)
    smb_files = [
        file.smb_info._asdict()
        for file in smb.scandir(smb_dir)
        if file.name.endswith('.mp4')
    ]
    local_files = list_local()
    # logger.info('[SYNC] Task starting')

    # logger.info(f"[SMB -> LOCAL] Syncing new files from SMB to local...")
    for file in smb_files:
        if file['file_name'] not in local_files:
            # logger.info(f"[SMB -> LOCAL] {file['file_name']} does not exist")
            with smb.open_file(str(Path(smb_dir) / file['file_name']), mode="rb") as smb_file:
                with open(local_dir / file['file_name'], mode="wb") as local_file:
                    local_file.write(smb_file.read())
                    # logger.info(
                    #     f"[SMB -> LOCAL] Saved file at {local_dir /  file['file_name']}")

        # else:
        #     logger.info(f"[SMB -> LOCAL] {file['file_name']} exists. Skipping!")
    stop = perf_counter()
    logger.info(f'[SMB -> LOCAL] Done in {stop-start}s')
    start = perf_counter()
    # logger.info("[LOCAL SYNC] Checking if local files need to be deleted...")
    for local_file in local_files:
        # If local file not present in smb
        if not any(d.get('file_name') == local_file for d in smb_files):
            # logger.info(
            #     f'[LOCAL SYNC] Removing file not present on SMB {local_dir /  local_file}')
            os.remove(local_dir / local_file)
        # else:
        #     logger.info(f'[LOCAL SYNC] {local_file} is present. Skipping')

    smb_session.disconnect()

    video_queue = list_local()

    if active_connections:
        if 'control' in active_connections:
            await active_connections['control'].send_json(
                {
                    "action": "update queue",
                    "message": video_queue
                })
            print('sent to ws control')

    get_next_vid = create_cycler(video_queue)

    stop = perf_counter()
    logger.info(f'[LOCAL SYNC] Done in {stop-start}s')


video_router = APIRouter(
    prefix="/video",
    tags=["Video"],
)


@video_router.get('/')
def next_video():
    return get_next_vid()


@video_router.get('/queue')
def next_video():
    return list_local()


@video_router.delete('/{filename}')
async def remove_video(filename: str):
    try:
        smb_session = smb.register_session(
            settings.SMB_HOST, username=settings.SMB_USERNAME, password=settings.SMB_PASSWORD)
        smb.remove(str(Path(smb_dir) / (filename + ".mp4")))
        smb_session.disconnect()
        await sync()
        return f"{filename + '.mp4'} removed"
    except Exception as e:
        logger.info(f'[VID] {e}')
        raise HTTPException(status_code=404, detail="Failed to delete video")


@video_router.post("/")
async def upload_video(file: UploadFile):

    try:
        smb_session = smb.register_session(
            settings.SMB_HOST, username=settings.SMB_USERNAME, password=settings.SMB_PASSWORD)
        with smb.open_file(str(Path(smb_dir) / file.filename), mode="wb") as fd:
            fd.write(await file.read())
        smb_session.disconnect()
        await sync()
        return {"message": f"{file.filename} uploaded"}
    except Exception as e:
        logger.info(f'[VID] {e}')
        raise HTTPException(status_code=500, detail="Failed to upload video")
