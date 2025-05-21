from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
import smbclient.path
from src.config import settings
import logging
import smbclient
from src.routers.ws import sync_frontend
from PIL import Image
from io import BytesIO
from pathlib import Path
import os
import filetype
logger = logging.getLogger('uvicorn.error')
router = APIRouter(prefix="/picture", tags=["Edit picture"])

# Helper to construct the full SMB path


def get_smb_path(filename: str) -> str:
    return os.path.join(fr'\\{settings.SMB_HOST}\\', *settings.SMB_FOLDER.split(','), filename)


@router.post("/{card_id}")
async def upload_file(card_id: int, file: UploadFile = File(...)):
    kind = filetype.guess(await file.read(2048))
    await file.seek(0)
    if kind is None or not kind.mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="Not a valid image")
    try:
        # Load the uploaded image into Pillow
        img = Image.open(BytesIO(await file.read()))
        output_buffer = BytesIO()
        # Always convert to PNG
        img.convert("RGB").save(output_buffer, format="PNG")

        # Reset buffer to the beginning
        output_buffer.seek(0)

        # Set final path with .png extension
        smb_path = get_smb_path(f"{card_id}.png")

        # Save to SMB
        with smbclient.open_file(smb_path, mode="wb") as dst:
            dst.write(output_buffer.read())

        logger.info(f"Uploaded and converted file to SMB: {smb_path}")
        await sync_frontend()
        return {"filename": f"{card_id}.png", "status": "success"}

    except Exception as e:
        logger.exception("Failed to upload or convert file.")
        raise HTTPException(status_code=500, detail="Upload failed")

    finally:
        await file.close()

@router.get("/{card_id}")
async def get_image(card_id: int):
    logger.info(f"getting stuff for {card_id}")
    filename = f"{card_id}.png"
    smb_path = get_smb_path(filename=filename)
    local_path = os.path.join(os.getcwd(), "public", filename)

    if not smbclient.path.exists(smb_path):
        logger.error(f"File not found for {card_id}")
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(local_path):
        try:
            with smbclient.open_file(smb_path, mode="rb") as src, open(local_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            logger.exception(f"Failed to download file: {e}")
            raise HTTPException(status_code=500, detail="Download failed")
    return FileResponse(local_path, filename=filename)


@router.delete("/{card_id}")
async def delete_file(card_id: int):
    filename = f"{card_id}.png"

    smb_path = get_smb_path(filename)

    if not smbclient.path.exists(smb_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        smbclient.remove(smb_path)
        os.remove(os.path.join(os.getcwd(), "public", filename))
        logger.info(f"Deleted file from SMB: {smb_path}")
        await sync_frontend()
        return {"status": "deleted", "filename": filename}
    except Exception as e:
        logger.exception("Failed to delete file.")
        raise HTTPException(status_code=500, detail="Delete failed")
