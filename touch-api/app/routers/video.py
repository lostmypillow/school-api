from fastapi import APIRouter, Response, UploadFile, HTTPException, BackgroundTasks
from typing import List, Iterable
# from smbclient import register_session, open_file, scandir
import smbclient as smb
from pathlib import Path
import logging
from pydantic import BaseModel
from itertools import cycle
from fastapi.responses import FileResponse
from app.lib.custom_logger import logger
from app.lib.create_cycler import create_cycler
from app.lib.list_local import list_local
from app.lib.sync import sync
import aiofiles
import os
from time import perf_counter
video_router = APIRouter(
    prefix="/video",
    tags=["Video"],
)

SMB_SERVER = os.getenv('SMB_SERVER')
SMB_USERNAME = os.getenv('SMB_USERNAME')
SMB_PASSWORD = os.getenv('SMB_PASSWORD')


smb_dir = f"\\\\{SMB_SERVER}\\\\"

# (root)/static
local_dir = Path(__file__).resolve().parent.parent.parent / "static"

video_queue: list[dict] = []




get_next_vid = create_cycler(video_queue)



# def list_local():
#     return [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]


# async def sync():
#     start = perf_counter()
#     smb_session = smb.register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD) 
#     smb_files = [
#         file.smb_info._asdict()
#         for file in smb.scandir(smb_dir)
#         if file.name.endswith('.mp4')
#     ]
#     local_files = list_local()
#     logger.info('[SYNC] Task starting')

#     logger.info(f"[SMB -> LOCAL] Syncing new files from SMB to local...")
#     for file in smb_files:
#         if file['file_name'] not in local_files:
#             logger.info(f"[SMB -> LOCAL] {file['file_name']} does not exist")
#             with smb.open_file(f"{smb_dir}\\{file['file_name']}", mode="rb") as smb_file:
#                 with open(f"{local_dir}\\{file['file_name']}", mode="wb") as local_file:
#                     local_file.write(smb_file.read())
#                     logger.info(
#                         f"[SMB -> LOCAL] Saved file at {local_dir /  file['file_name']}")

#         else:
#             logger.info(f"[SMB -> LOCAL] {file['file_name']} exists. Skipping!")
#     stop = perf_counter()
#     start = perf_counter() 
#     logger.info(f'[SMB -> LOCAL] Done in {stop-start}s')
#     logger.info("[LOCAL SYNC] Checking if local files need to be deleted...")
#     for local_file in local_files:
#         # If local file not present in smb
#         if not any(d.get('file_name') == local_file for d in smb_files):
#             logger.info(
#                 f'[LOCAL SYNC] Removing file not present on SMB {local_dir /  local_file}')
#             os.remove(local_dir / local_file)
#         else:
#             logger.info(f'[LOCAL SYNC] {local_file} is present. Skipping')
    
#     smb_session.disconnect()

#     if active_connections:
#         for client in active_connections:
#             await active_connections[client].send_json({
#                 "from": "server",
#                 "to": "all",
#                 "action": "update queue",
#                 "data": list_local()
#             })
#     stop = perf_counter()
#     logger.info(f'[LOCAL SYNC] Done in {stop-start}s')




@video_router.get('/sync')
def sync_video(bg_tasks: BackgroundTasks):
    try:
        
        bg_tasks.add_task(sync)
        
        return "Sync queued"
    except Exception as e:
        logger.info(f'[VID] {e}')
        raise HTTPException(status_code=404, detail="Failed to get queue")
    


@video_router.delete('/{filename}')
def remove_video(filename: str, bg_tasks: BackgroundTasks):
    try:
        smb_session = smb.register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD) 
        smb.remove(f"{smb_dir}\\{filename + '.mp4'}")
        bg_tasks.add_task(sync)
        smb_session.disconnect()
        return f"{filename + '.mp4'} removed"
    except Exception as e:
        logger.info(f'[VID] {e}')
        raise HTTPException(status_code=404, detail="Failed to delete video")
   


@video_router.post("/")
async def upload_video(file: UploadFile, bg_tasks: BackgroundTasks):

    try:
        smb_session = smb.register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD) 
        with smb.open_file(f"{smb_dir}\\{file.filename}", mode="wb") as fd:
            fd.write(await file.read())
        bg_tasks.add_task(sync)
        smb_session.disconnect()
        return {"message": f"{file.filename} uploaded"}
    except Exception as e:
        logger.info(f'[VID] {e}')
        raise HTTPException(status_code=500, detail="Failed to upload video")