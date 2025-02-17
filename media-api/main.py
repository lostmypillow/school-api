import logging
import os
import psutil
from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File
from fastapi.responses import StreamingResponse
import smbclient
from config import settings
from itertools import cycle
# Initialize FastAPI
app = FastAPI(
    title="",
    description="Handles streams and uploads for  (for now)",
    version="0.1.0")

# SMB Configuration
SMB_SERVER = settings.SMB_HOST
SMB_SHARE = settings.SMB_FOLDER
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



def get_file_size(file_name: str):
    """Get the total size of the file on SMB using smbclient."""
    smbclient.ClientConfig(username=SMB_USERNAME, password=SMB_PASSWORD)

    # Get the file size from the SMB share
    file_path = f"\\\\{SMB_SERVER}\\{SMB_SHARE}\\{file_name}"
    size = os.stat(file_path).st_size

    logging.info(f"File size: {size} bytes")
    return size


def stream_smb_file(file_name: str, start: int, end: int):
    """Stream file from SMB using smbclient while logging memory usage and chunk progress."""
    logging.info(f"Starting stream: {start}-{end}")

    smbclient.ClientConfig(username=SMB_USERNAME, password=SMB_PASSWORD)
    file_path = f"\\\\{SMB_SERVER}\\{SMB_SHARE}\\{file_name}"

    with smbclient.open_file(file_path, mode='rb') as file:
        file.seek(start)
        while file.tell() < end:
            check_memory_usage()  # Ensure we don’t exceed RAM limit

            chunk_size = min(CHUNK_SIZE, end - file.tell() + 1)
            chunk = file.read(chunk_size)
            if not chunk:
                break  # End of file

            logging.info(
                f"Streaming chunk: Offset={file.tell()}, Size={len(chunk)} bytes")

            yield chunk

    logging.info("Streaming finished successfully")


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
    global get_next_vid, video_queue
    smbclient.ClientConfig(username=SMB_USERNAME, password=SMB_PASSWORD)
    file_path = f"\\\\{SMB_SERVER}\\{SMB_SHARE}"
    try:
        return [
            file.smb_info._asdict()["file_name"]
            for file in smbclient.scandir(file_path)
            if file.name.endswith('.mp4')
        ]
    except Exception as e:
        print(e)
        return []


@app.get("/video/{file_name}")
async def get_video(file_name: str, request: Request, range: str = Header(None)):
    """Handle range requests and stream the video with logging."""
    check_memory_usage()

    file_size = get_file_size(file_name)
    start, end = 0, file_size - 1  # Default full file range

    if range:
        try:
            range_values = range.replace("bytes=", "").split("-")
            start = int(range_values[0]) if range_values[0] else 0
            end = int(range_values[1]) if len(
                range_values) > 1 and range_values[1] else file_size - 1
        except ValueError:
            logging.error("Invalid Range header received")
            raise HTTPException(status_code=400, detail="Invalid Range header")

    if start >= file_size or end >= file_size:
        logging.warning(
            f"Invalid range: {start}-{end} (File size: {file_size})")
        raise HTTPException(
            status_code=416, detail="Requested Range Not Satisfiable")

    logging.info(f"Processing range request: {start}-{end}/{file_size}")

    response_headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }

    return StreamingResponse(stream_smb_file(file_name, start, end), status_code=206, headers=response_headers)


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video to SMB share in chunks."""
    check_memory_usage()  # Check memory usage before starting the upload

    # Ensure the video queue is updated, in case it changes during upload
    global video_queue, get_next_vid
    smbclient.ClientConfig(username=SMB_USERNAME, password=SMB_PASSWORD)
    file_path = f"\\\\{SMB_SERVER}\\{SMB_SHARE}\\{file.filename}"

    # Open the file on SMB for writing
    with smbclient.open_file(file_path, mode='wb') as smb_file:
        # Stream the uploaded file in chunks
        while chunk := await file.read(CHUNK_SIZE):
            check_memory_usage()  # Check memory usage during the upload process
            smb_file.write(chunk)
            logging.info(f"Uploaded chunk of size {len(chunk)} bytes")

    logging.info(f"Successfully uploaded {file.filename} to SMB share.")
    return {"message": f"File '{file.filename}' uploaded successfully"}


@app.delete("/video/{file_name}")
async def delete_video(file_name: str):
    """Delete a video file from the SMB share."""
    check_memory_usage()  # Check memory usage before starting the delete operation

    # Configure smbclient with credentials
    smbclient.ClientConfig(username=SMB_USERNAME, password=SMB_PASSWORD)
    file_path = f"\\\\{SMB_SERVER}\\{SMB_SHARE}\\{file_name}"

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
