from fastapi import APIRouter, Response, UploadFile, HTTPException
from typing import List
from smbclient import register_session, open_file, scandir
from pathlib import Path
import logging
from pydantic import BaseModel
from itertools import cycle
from fastapi.responses import FileResponse
import aiofiles
router = APIRouter(
    prefix="/video",
    tags=["Video"],
)


# In-memory video queue
video_queue = []
video_queue_cycle = cycle(video_queue)

# Define the video model for API responses


class VideoItem(BaseModel):
    id: int
    title: str
    url: str


# Get the base directory where the script is running
base_dir = Path(__file__).resolve()
static_dir = base_dir.parent.parent.parent / "static" / "videos"  # Relative path to static/videos

# Ensure the local videos directory exists
static_dir.mkdir(parents=True, exist_ok=True)

# SMB Credentials and Server Info
SMB_SERVER = ""
SMB_USERNAME = 
SMB_PASSWORD = 

# SMB session registration


def register_smb_session():
    register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD)


def check_smb():
    global video_queue_cycle
    try:
        smb_dir = f"\\\\{SMB_SERVER}\\\\"

        smb_files = [{"name": entry.name, "path": entry.path}
                     for entry in scandir(smb_dir) if entry.name.endswith('.mp4')]

        files_not_in_local = [file for file in smb_files if not (
            static_dir / file['name']).exists()]

        for fi in files_not_in_local:

            with open_file(fi['path'], mode="rb") as smb_file:
                video_path = static_dir / fi['name']
                with open(video_path, mode="wb") as local_file:
                    local_file.write(smb_file.read())

        print("files not in local resolved")
        
        files_in_local = [
            file.name for file in static_dir.iterdir() if file.is_file()]
        matches_not_found = []
        
        for item in files_in_local:
            if not any(d.title == item for d in video_queue):
                matches_not_found.append(item)
        print("1")

        for item in matches_not_found:
            video_item = VideoItem(
                id=len(video_queue) + 1, title=item, url=f"/static/videos/{item}")
            video_queue.append(video_item)
            video_queue_cycle = cycle(video_queue)
        print("2")

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Failed to check SMB server")
@router.get("/queue")
async def get_video_queue():
    register_smb_session()
    check_smb()
    return video_queue

async def stream_video(video_path):
    async with aiofiles.open(video_path, 'rb') as f:
        while True:
            chunk = await f.read(1024)
            if not chunk:
                break
            yield chunk

# FastAPI route for streaming video
@router.get("/play/{num}")
async def stream_video_route(num: int):
    register_smb_session()
    check_smb()
    print("4")
    if not video_queue:
        raise HTTPException(status_code=404, detail="No videos in the queue")

    # Get the next video item in the cycle
    video_item = video_queue[num]
    print("5")
    video_path = static_dir/ video_item.title

    # Check if the video file exists
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    print("6")
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        headers={"Content-Disposition": f"inline; filename={video_item.title}"}
    )

    # Stream the video in chunks
    # return StreamingResponse(
    #     stream_video(video_path),
    #     media_type="video/mp4",
    #     headers={"Content-Disposition": f"inline; filename={video_item.title}"}
    # )

@router.post("/upload")
async def upload_video(file: UploadFile):
    # Register the SMB session
    register_smb_session()

    # Define the SMB path where the video will be uploaded
    smb_path = f"\\\\{SMB_SERVER}\\\\\\{file.filename}"

    try:
        # Save the uploaded file to the SMB share
        with open_file(smb_path, mode="wb") as fd:
            fd.write(await file.read())

        # Save the video to the local static directory for streaming
        local_video_path = static_dir / file.filename
        with open(local_video_path, mode="wb") as local_file:
            local_file.write(await file.read())

        # Add video to the queue (you can customize the title and url here)
        video_item = VideoItem(id=len(
            video_queue) + 1, title=file.filename, url=f"/static/videos/{file.filename}")
        video_queue.append(video_item)

        # Recreate the cycle iterator whenever a video is added to the queue
        global video_queue_cycle
        video_queue_cycle = cycle(video_queue)

        return {"message": f"Video {file.filename} uploaded and added to the queue", "video_queue": video_queue}
    except Exception as e:
        log.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload video")


# @router.get("/video/{video_name}")
# async def serve_video(video_name: str):
#     video_path = static_dir / video_name
#     if video_path.exists():
#         with open(video_path, mode="rb") as file:
#             video_bytes = file.read()
#         return Response(
#             content=video_bytes,
#             media_type="video/mp4",
#             headers={"Content-Disposition": f"inline; filename={video_name}"}
#         )
#     else:
#         raise HTTPException(status_code=404, detail="Video not found")
