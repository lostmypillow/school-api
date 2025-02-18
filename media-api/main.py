import logging
import os
import psutil
from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File
from fastapi.responses import StreamingResponse
import smbclient
from config import settings
from itertools import cycle
import asyncio
# Initialize FastAPI
app = FastAPI(
    title="",
    description="Handles streams and uploads for  (for now)",
    version="0.1.0")

# SMB Configuration
smb_url = ''
SMB_USERNAME = settings.SMB_USERNAME
SMB_PASSWORD = settings.SMB_PASSWORD
CHUNK_SIZE = 512 * 1024  # 512 KB chunks
MEMORY_LIMIT_MB = 500  # Max memory usage (500MB)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("fastapi_memory.log"),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console
    ],
)


def check_memory_usage():
    """Check and log current memory usage."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    memory_usage_mb = mem_info.rss / (1024 * 1024)  # Convert to MB

    logging.info(f"Memory Usage: {memory_usage_mb:.2f}MB")

    if memory_usage_mb > MEMORY_LIMIT_MB:
        logging.warning(
            f"Memory limit exceeded! Usage: {memory_usage_mb:.2f}MB")
        raise HTTPException(status_code=503, detail="Memory limit exceeded")


video_queue = []


def create_cycler(iterable: list):
    cycler: cycle = cycle(iterable)

    def next_video() -> str:
        return next(cycler, None)
    return next_video


get_next_vid = create_cycler(video_queue)

def open_smb_session():
    smbclient.register_session(server="", username=SMB_USERNAME, password=SMB_PASSWORD)

def close_smb_session():
    try:
        # Check if the session and file handle are open
        smbclient.reset_connection_cache()  # Close all connections if still active
    except Exception as e:
        logging.error(f"Error closing SMB session: {e}")


def get_file_size(file_name: str):
    """Get the total size of the file on SMB using smbclient."""
    open_smb_session()
    for file in smbclient.scandir(smb_url):
        if file.name == file_name:
            return file.smb_info._asdict()["end_of_file"]
    close_smb_session()


async def stream_smb_file(file_name: str, start: int, end: int):
    """Stream file from SMB using smbclient while logging memory usage and chunk progress."""
    file_path = os.path.join(smb_url, file_name)

    open_smb_session()
    try:
        with smbclient.open_file(file_path, mode='rb') as file:
            file.seek(start)
            while file.tell() < end:
                chunk_size = min(CHUNK_SIZE, end - file.tell() + 1)
                chunk = file.read(chunk_size)
                if not chunk:
                    break  # End of file

                logging.info(f"Streaming chunk: Offset={file.tell()}, Size={len(chunk)} bytes")

                try:
                    yield chunk
                except asyncio.CancelledError:
                    logging.warning("Client disconnected during streaming.")
                    break  # Stop streaming if the client disconnects
    finally:
        close_smb_session()  # Close the SMB session once done or on disconnect


def get_all_smb_files():
    open_smb_session()
    try:
        files =  [
            file.smb_info._asdict()["file_name"]
            for file in smbclient.scandir(smb_url)
            if file.name.endswith('.mp4')
        ]
    except Exception as e:
        print(e)
        files = []
    finally:
        close_smb_session()
        return files
    


@app.middleware("http")
async def limit_memory_usage(request: Request, call_next):
    """Middleware to check memory usage before and after requests."""
    logging.info(f"Incoming request: {request.url}")
    check_memory_usage()

    response = await call_next(request)

    check_memory_usage()
    return response


@app.get('/next')
def get_next_file():
    global get_next_vid, video_queue


    updated_queue = get_all_smb_files()
    if video_queue != updated_queue:
        video_queue = updated_queue
        get_next_vid = create_cycler(video_queue)

    return get_next_vid()


@app.get('/all')
def get_all_files():
    return get_all_smb_files()


@app.get("/video/{file_name}")
async def get_video(file_name: str, request: Request, range: str = Header(None)):
    """Handle range requests and stream the video with logging."""
    check_memory_usage()
    open_smb_session()

    file_size = get_file_size(file_name)
    start, end = 0, file_size - 1  # Default full file range

    if range:
        try:
            range_values = range.replace("bytes=", "").split("-")
            start = int(range_values[0]) if range_values[0] else 0
            end = int(range_values[1]) if len(range_values) > 1 and range_values[1] else file_size - 1
        except ValueError:
            logging.error("Invalid Range header received")
            close_smb_session()
            raise HTTPException(status_code=400, detail="Invalid Range header")

    if start >= file_size or end >= file_size:
        logging.warning(f"Invalid range: {start}-{end} (File size: {file_size})")
        close_smb_session()
        raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

    logging.info(f"Processing range request: {start}-{end}/{file_size}")

    response_headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }

    try:
        return StreamingResponse(stream_smb_file(file_name, start, end), status_code=206, headers=response_headers)
    except asyncio.CancelledError:
        logging.warning(f"Client disconnected before completing stream for {file_name}.")
        close_smb_session()
        raise  # Re-raise the exception to ensure proper error handling



@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    open_smb_session()
    """Upload video to SMB share in chunks."""
    check_memory_usage()  # Check memory usage before starting the upload

    # Ensure the video queue is updated, in case it changes during upload
    global video_queue, get_next_vid

    try:
        file_path = smb_url + "/" + file.filename
        # return file_path

        print('Open the file on SMB for writing')
        with smbclient.open_file(file_path, mode='wb') as smb_file:
            print('Stream the uploaded file in chunks')
            while chunk := await file.read(CHUNK_SIZE):
                check_memory_usage()  
                print('Check memory usage during the upload process')
                smb_file.write(chunk)
                logging.info(f"Uploaded chunk of size {len(chunk)} bytes")

        logging.info(f"Successfully uploaded {file.filename} to SMB share.")
        
        return {"message": f"File '{file.filename}' uploaded successfully"}
    except Exception as e:
        print(e)
    finally:
        close_smb_session()

async def write_to_smb(file: UploadFile, file_path: str):
    """Writes an uploaded file to SMB in chunks."""
    with smbclient.open_file(file_path, mode="wb") as smb_file:
        while True:
            chunk = await file.read(CHUNK_SIZE)  # Read chunk asynchronously
            if not chunk:
                break  # Stop when the file is fully read
            await asyncio.to_thread(smb_file.write, chunk)  # Write in a separate thread
            logging.info(f"Uploaded {len(chunk)} bytes")

# @app.post("/upload")
# async def upload_video(file: UploadFile = File(...)):
#     """Upload a large video file to SMB share using streaming."""
#     open_smb_session()
    
#     try:
#         file_path = f"{smb_url}/{file.filename}"
#         await write_to_smb(file, file_path)  # Stream file upload
#         logging.info(f"Successfully uploaded {file.filename}")
#         return {"message": f"File '{file.filename}' uploaded successfully"}
#     except Exception as e:
#         logging.error(f"Upload failed: {e}")
#         return {"error": str(e)}
#     finally:
#         close_smb_session()

@app.delete("/video/{file_name}")
async def delete_video(file_name: str):
    open_smb_session()
    """Delete a video file from the SMB share."""
    check_memory_usage()  # Check memory usage before starting the delete operation

    file_path = os.path.join(smb_url, file_name)

    try:
        # Check if the file exists before trying to delete
        if not smbclient.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Delete the file from the SMB share
        smbclient.remove(file_path)
        logging.info(f"Successfully deleted file: {file_name}")

        return {"message": f"File '{file_name}' deleted successfully"}

    except Exception as e:
        # Log the exception and return an error response
        logging.error(f"Error deleting file {file_name}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting file: {str(e)}")
    finally:
        close_smb_session()
