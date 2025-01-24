
# from smbclient import register_session, open_file, scandir
import smbclient as smb
from app.lib.active_connections import active_connections
from app.lib.custom_logger import logger
from app.lib.list_local import list_local, local_dir
import os
from pathlib import Path
from time import perf_counter
from app.lib.create_cycler import create_cycler
SMB_SERVER = os.getenv('SMB_SERVER')
SMB_USERNAME = os.getenv('SMB_USERNAME')
SMB_PASSWORD = os.getenv('SMB_PASSWORD')


smb_dir = f"\\\\{SMB_SERVER}\\\\"


video_queue: list = []
get_next_vid = None
async def sync():
    global active_connections
    global video_queue
    start = perf_counter()
    smb_session = smb.register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD) 
    smb_files = [
        file.smb_info._asdict()
        for file in smb.scandir(smb_dir)
        if file.name.endswith('.mp4')
    ]
    local_files = list_local()
    logger.info('[SYNC] Task starting')

    logger.info(f"[SMB -> LOCAL] Syncing new files from SMB to local...")
    for file in smb_files:
        if file['file_name'] not in local_files:
            logger.info(f"[SMB -> LOCAL] {file['file_name']} does not exist")
            with smb.open_file(f"{smb_dir}\\{file['file_name']}", mode="rb") as smb_file:
                with open(f"{local_dir}\\{file['file_name']}", mode="wb") as local_file:
                    local_file.write(smb_file.read())
                    logger.info(
                        f"[SMB -> LOCAL] Saved file at {local_dir /  file['file_name']}")

        else:
            logger.info(f"[SMB -> LOCAL] {file['file_name']} exists. Skipping!")
    stop = perf_counter()
    start = perf_counter() 
    logger.info(f'[SMB -> LOCAL] Done in {stop-start}s')
    logger.info("[LOCAL SYNC] Checking if local files need to be deleted...")
    for local_file in local_files:
        # If local file not present in smb
        if not any(d.get('file_name') == local_file for d in smb_files):
            logger.info(
                f'[LOCAL SYNC] Removing file not present on SMB {local_dir /  local_file}')
            os.remove(local_dir / local_file)
        else:
            logger.info(f'[LOCAL SYNC] {local_file} is present. Skipping')
    
    smb_session.disconnect()

    for video in list_local():
        video_queue.append(video)

    if active_connections:
        for client in active_connections:
            await active_connections[client].send_json({
                "from": "server",
                "action": "sync",
                "message": video_queue
            })
    
    stop = perf_counter()
    logger.info(f'[LOCAL SYNC] Done in {stop-start}s')
