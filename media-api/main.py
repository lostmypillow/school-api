import logging
import os
import shutil
from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
import smbclient
from config import settings
from itertools import cycle
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Initialize FastAPI


# Configuration
smb_url = ''
SMB_USERNAME = settings.SMB_USERNAME
SMB_PASSWORD = settings.SMB_PASSWORD
CHUNK_SIZE = 512 * 1024  # 512 KB
STATIC_FOLDER = './static'

# Configure logging

def open_smb_session():
    smbclient.register_session(server="", username=SMB_USERNAME, password=SMB_PASSWORD)

def close_smb_session():
    try:
        smbclient.reset_connection_cache()
    except Exception as e:
        logging.error(f"Error closing SMB session: {e}")
video_cycler = None
def sync_from_smb():
    global video_cycler
    """Sync files from SMB to local static folder."""
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    open_smb_session()
    try:
        for file in smbclient.scandir(smb_url):
            if file.name.endswith('.mp4'):
                local_file_path = os.path.join(STATIC_FOLDER, file.name)
                if not os.path.exists(local_file_path):
                    logging.info(f"Downloading {file.name} from SMB")
                    with smbclient.open_file(os.path.join(smb_url, file.name), mode='rb') as smb_file:
                        with open(local_file_path, 'wb') as local_file:
                            shutil.copyfileobj(smb_file, local_file)
                    logging.info(f"Downloaded {file.name}")
                else:
                    logging.info(f"{file.name} exists. Skipping.")
    except Exception as e:
        logging.error(f"Error syncing files from SMB: {e}")
    finally:
        video_cycler = cycle([f for f in os.listdir(STATIC_FOLDER) if f.endswith('.mp4')])
        close_smb_session()



@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting app, syncing files from SMB...")
    sync_from_smb()
    yield
    logging.info("Shutting down app...")





app = FastAPI(
    title="",
    lifespan=lifespan,
    description="Handles streams and uploads for  (for now)",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/next')
def get_next_file():
    """Return the next file in the local static folder."""
    files = [f for f in os.listdir(STATIC_FOLDER) if f.endswith('.mp4')]
    if not files:
        raise HTTPException(status_code=404, detail="No files available")
    return next(video_cycler, None)


@app.get('/all')
def get_all_files():
    """List all files in the local static folder."""
    return [f for f in os.listdir(STATIC_FOLDER) if f.endswith('.mp4')]

@app.get("/video/{file_name}")
async def get_video(file_name: str, request: Request, range: str = Header(None)):
    """Serve video files directly from the static folder."""
    file_path = os.path.join(STATIC_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    start, end = 0, file_size - 1

    if range:
        range_values = range.replace("bytes=", "").split("-")
        start = int(range_values[0]) if range_values[0] else 0
        end = int(range_values[1]) if len(range_values) > 1 and range_values[1] else file_size - 1

        if start >= file_size or end >= file_size:
            raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }

    return FileResponse(file_path, headers=headers, status_code=206)

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video to SMB and sync to local static folder."""
    open_smb_session()
    file_path = os.path.join(smb_url, file.filename)

    try:
        # Upload to SMB
        with smbclient.open_file(file_path, mode='wb') as smb_file:
            while chunk := await file.read(CHUNK_SIZE):
                smb_file.write(chunk)

        # Sync to local static folder
        local_file_path = os.path.join(STATIC_FOLDER, file.filename)
        with smbclient.open_file(file_path, mode='rb') as smb_file:
            with open(local_file_path, 'wb') as local_file:
                shutil.copyfileobj(smb_file, local_file)

        logging.info(f"Uploaded {file.filename} and synced to static folder.")
        return {"message": f"File '{file.filename}' uploaded successfully"}
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    finally:
        close_smb_session()

@app.delete("/video/{file_name}")
async def delete_video(file_name: str):
    """Delete video from SMB and local static folder."""
    open_smb_session()
    smb_file_path = os.path.join(smb_url, file_name)

    try:
        # Delete from SMB
        if smbclient.path.exists(smb_file_path):
            smbclient.remove(smb_file_path)
            logging.info(f"Deleted {file_name} from SMB")

        # Delete from local static folder
        local_file_path = os.path.join(STATIC_FOLDER, file_name)
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            logging.info(f"Deleted {file_name} from local storage")

        return {"message": f"File '{file_name}' deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting file {file_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")
    finally:
        close_smb_session()
