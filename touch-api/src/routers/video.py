from fastapi import APIRouter, Response, UploadFile, HTTPException, BackgroundTasks
from typing import List, Iterable
# from smbclient import register_session, open_file, scandir
import smbclient as smb
from pathlib import Path
import logging
from pydantic import BaseModel
from itertools import cycle
from fastapi.responses import FileResponse
import aiofiles
import os
router = APIRouter(
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


def create_cycler(iterable: Iterable):
    cycler = cycle(iterable)

    def next_video():
        return next(cycler)
    return next_video


get_next_vid = create_cycler(video_queue)


# Register SMB session to be reused
smb_session = smb.register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD)

def list_local():
    return [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]


def sync():
    smb_files = [
        file.smb_info._asdict()
        for file in smb.scandir(smb_dir)
        if file.name.endswith('.mp4')
    ]
    local_files = list_local()
    print('[SYNC] Task starting')

    print(f"[SMB -> LOCAL] Syncing new files from SMB to local...")
    for file in smb_files:
        if file['file_name'] not in local_files:
            print(f"[SMB -> LOCAL] {file['file_name']} does not exist")
            with smb.open_file(f"{smb_dir}\\{file['file_name']}", mode="rb") as smb_file:
                with open(f"{local_dir}\\{file['file_name']}", mode="wb") as local_file:
                    local_file.write(smb_file.read())
                    print(
                        f"[SMB -> LOCAL] Saved file at {local_dir /  file['file_name']}")

        else:
            print(f"[SMB -> LOCAL] {file['file_name']} exists. Skipping!")
    print("[LOCAL] Checking if local files need to be deleted...")
    for local_file in local_files:
        # If local file not present in smb
        if not any(d.get('file_name') == local_file for d in smb_files):
            print(
                f'[LOCAL] Removing file not present on SMB {local_dir /  local_file}')
            os.remove(local_dir / local_file)
        else:
            print(f'[LOCAL] {local_file} is present. Skipping')
    print('[SYNC] Done!')


@router.get('/sync')
def sync_video(bg_tasks: BackgroundTasks):
    bg_tasks.add_task(sync)
    return "Sync queued"


@router.delete('/{filename}')
def remove_video(filename: str):
    try:
        smb.remove(f"{smb_dir}\\{filename + '.mp4'}")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Failed to delete video")
    return f"{filename + '.mp4'} removed"


@router.post("/")
async def upload_video(file: UploadFile):

    try:
        with smb.open_file(f"{smb_dir}\\{file.filename}", mode="wb") as fd:
            fd.write(await file.read())
        return {"message": f"{file.filename} uploaded"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload video")


# def register_smb_session():
#


# def check_smb():
#     global video_queue_cycle
#     try:


#         smb_files =

#         files_not_in_local = [file for file in smb_files if not (
#             static_dir / file['name']).exists()]

#         for fi in files_not_in_local:

#             with open_file(fi['path'], mode="rb") as smb_file:
#                 video_path = static_dir / fi['name']
#                 with open(video_path, mode="wb") as local_file:
#                     local_file.write(smb_file.read())

#         print("files not in local resolved")

#         files_in_local = [
#             file.name for file in static_dir.iterdir() if file.is_file()]
#         matches_not_found = []

#         for item in files_in_local:
#             if not any(d.title == item for d in video_queue):
#                 matches_not_found.append(item)
#         print("1")

#         for item in matches_not_found:
#             video_item = VideoItem(
#                 id=len(video_queue) + 1, title=item, url=f"/static/videos/{item}")
#             video_queue.append(video_item)
#             video_queue_cycle = cycle(video_queue)
#         print("2")

#     except Exception as e:
#         print(e)
#         raise HTTPException(
#             status_code=500, detail="Failed to check SMB server")
# @router.get("/queue")
# async def get_video_queue():
#     register_smb_session()
#     check_smb()
#     return video_queue

# async def stream_video(video_path):
#     async with aiofiles.open(video_path, 'rb') as f:
#         while True:
#             chunk = await f.read(1024)
#             if not chunk:
#                 break
#             yield chunk

# # FastAPI route for streaming video
# @router.get("/play/{num}")
# async def stream_video_route(num: int):
#     register_smb_session()
#     check_smb()
#     print("4")
#     if not video_queue:
#         raise HTTPException(status_code=404, detail="No videos in the queue")

#     # Get the next video item in the cycle
#     video_item = video_queue[num]
#     print("5")
#     video_path = static_dir/ video_item.title

#     # Check if the video file exists
#     if not video_path.exists():
#         raise HTTPException(status_code=404, detail="Video file not found")
#     print("6")
#     return FileResponse(
#         path=video_path,
#         media_type="video/mp4",
#         headers={"Content-Disposition": f"inline; filename={video_item.title}"}
#     )

#     # Stream the video in chunks
#     # return StreamingResponse(
#     #     stream_video(video_path),
#     #     media_type="video/mp4",
#     #     headers={"Content-Disposition": f"inline; filename={video_item.title}"}
#     # )
