from rich.logging import RichHandler
from rich.traceback import install
import logging

install(show_locals=True)
rich_handler = RichHandler(rich_tracebacks=True)
logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[rich_handler]
)
for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
    logger = logging.getLogger(name)
    logger.handlers = [rich_handler]
    logger.setLevel(logging.INFO)

logger = logging.getLogger("rich")

import os
import shutil
from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse, PlainTextResponse
import smbclient
from config import settings
from itertools import cycle
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
import tomllib
from pathlib import Path as pathlib_Path
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

# Static variables
# TODO move them to .env
SMB_URL = f'//{settings.SMB_HOST}{settings.SMB_FOLDER}'
SMB_USERNAME = settings.SMB_USERNAME
SMB_PASSWORD = settings.SMB_PASSWORD
CHUNK_SIZE = 512 * 1024  # 512 KB
STATIC_FOLDER = './static'
video_cycler = None

# Configure logging


def open_smb_session():
    try:
        smbclient.register_session(
            server="", username=SMB_USERNAME, password=SMB_PASSWORD)
    except Exception as e:
        logging.error(f"Error opening SMB session: {e}")


def close_smb_session():
    try:
        smbclient.reset_connection_cache()
    except Exception as e:
        logging.error(f"Error closing SMB session: {e}")


def sync_from_smb():
    global video_cycler
    """Sync files from SMB to local static folder."""
    if not os.path.exists(STATIC_FOLDER):
        os.makedirs(STATIC_FOLDER)

    open_smb_session()
    try:
        for file in smbclient.scandir(SMB_URL):
            if file.name.endswith('.mp4'):
                local_file_path = os.path.join(STATIC_FOLDER, file.name)
                if not os.path.exists(local_file_path):
                    logging.info(f"Downloading {file.name} from SMB")
                    with smbclient.open_file(os.path.join(SMB_URL, file.name), mode='rb') as smb_file:
                        with open(local_file_path, 'wb') as local_file:
                            shutil.copyfileobj(smb_file, local_file)
                    logging.info(f"Downloaded {file.name}")
                else:
                    logging.info(f"{file.name} exists. Skipping.")
    except Exception as e:
        logging.error(f"Error syncing files from SMB: {e}")
    finally:
        video_cycler = cycle([f for f in os.listdir(
            STATIC_FOLDER) if f.endswith('.mp4')])
        close_smb_session()



current_file = pathlib_Path(__file__).resolve()
backend_pyproject_path = current_file.parent.parent / "pyproject.toml"
with backend_pyproject_path.open("rb") as f:
    backend_data = tomllib.load(f)
title = backend_data.get("project", {}).get("name", "Kw FastAPI Project")
version = backend_data.get("project", {}).get("version", "0.0.0")
description = backend_data.get("project", {}).get("description", "description here")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting app, syncing files from SMB...")
    # sync_from_smb()
    yield
    logging.info("Shutting down app...")


app = FastAPI(
    title=title,
    description=description,
    version=version,
    docs_url=None,
    redoc_url=None,
    root_path="/api/media",
    lifespan=lifespan,

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_local_filenames() -> list[str]:
    return [
        filename
        for filename in os.listdir(STATIC_FOLDER)
        if filename.endswith('.mp4')
    ]
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.root_path + app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url=app.root_path + "/static/swagger-ui-bundle.js",
        swagger_css_url=app.root_path + "/static/swagger-ui.css",
        swagger_favicon_url=app.root_path + "/static/favicon.ico",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get('/next', response_model=str, response_class=PlainTextResponse, responses={
    200: {
        "description": "Returns the next video filename from the static folder",
        "content": {
            "text/plain": {
                "example": "example_video.mp4"
            }
        }
    },
    404: {
        "description": "No files available",
        "content": {
            "application/json": {
                "example": {"detail": "No files available"}
            }
        }
    }
})
def get_next_file():
    """Return the next file in the local static folder.

    Returns
    -------
    str
        File name of the next file (e.g. xxx.mp4)

    Raises
    ------
    HTTPException
        When there are no files available
    """
    files: list[str] = get_local_filenames()
    if not files:

        raise HTTPException(status_code=404, detail="No files available")

    return next(video_cycler, None)


@app.get('/all', response_model=list[str], responses={
    200: {
        "description": "List of available .mp4 files",
        "content": {
            "application/json": {
                "example": ["video1.mp4", "video2.mp4"]
            }
        }
    }
})
def get_all_files() -> list[str]:
    """Returns a list of .mp4 filenames from the server's local static folder

    Returns
    -------
    list[str]
        List of .mp4 filenames from the server's local static folder
    """
    return get_local_filenames()

#  """Serve video files directly from the static folder."""


@app.get("/video/{file_name}")
async def get_video(file_name: str, request: Request, range: str = Header(None)):
    """Fetches video from local static folder. Advise hitting this endpoint by typing the full URL in address bar.

    Parameters
    ----------
    file_name : str
        filename, duh. E.g. xxx.mp4
    
    request : Request
        Unsure of what it's for, too scared to remove
    
    range : str, optional
        _description_, by default Header(None). Also unsure of what it's for, too scared to remove

    Returns
    -------
    FileResponse
        FastAPI FileResponse: https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse

    Raises
    ------
    HTTPException
        status_code=404, detail="File not found"
    HTTPException
        status_code=416, detail="Requested Range Not Satisfiable"
    """
    file_path = os.path.join(STATIC_FOLDER, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    start, end = 0, file_size - 1

    if range:
        range_values = range.replace("bytes=", "").split("-")
        start = int(range_values[0]) if range_values[0] else 0
        end = int(range_values[1]) if len(
            range_values) > 1 and range_values[1] else file_size - 1

        if start >= file_size or end >= file_size:
            raise HTTPException(
                status_code=416, detail="Requested Range Not Satisfiable")

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }

    return FileResponse(file_path, headers=headers, status_code=206)

# """Upload video to SMB and sync to local static folder."""
@app.post("/upload", responses={
    200: {
        "description": "Successful upload",
        "content": {
            "application/json": {
                "example": {"message": "File 'video1.mp4' uploaded successfully"}
            }
        }
    },
    500: {
        "description": "Upload failed",
        "content": {
            "application/json": {
                "example": {"detail": "Upload failed: [error message]"}
            }
        }
    }
})
async def upload_video(file: UploadFile = File(...)):
    """_summary_

    Parameters
    ----------
    file : UploadFile, optional
        _description_, by default File(...)

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    HTTPException
        _description_
    """
    open_smb_session()
    file_path = os.path.join(SMB_URL, file.filename)

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

#     """Delete video from SMB and local static folder."""
@app.delete("/video/{file_name}")
async def delete_video(file_name: str):
    """_summary_

    Parameters
    ----------
    file_name : str
        _description_

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    HTTPException
        _description_
    """
    open_smb_session()
    smb_file_path = os.path.join(SMB_URL, file_name)

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
