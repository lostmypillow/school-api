from typing import Iterable
import smbclient as smb
from pathlib import Path
from itertools import cycle
import os
import pprint

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
smb.register_session(SMB_SERVER, username=SMB_USERNAME, password=SMB_PASSWORD)
print("meow")
smb_files = [
    file.smb_info._asdict()
    for file in smb.scandir(smb_dir)
    if file.name.endswith('.mp4')
]

for file in smb_files:
    if not (local_dir / file['file_name']).exists():
        print(f"{file['file_name']} does not exist")
        with smb.open_file(f"{smb_dir}\\{file['file_name']}", mode="rb") as smb_file:
            with open(f"{local_dir}\\{file['file_name']}", mode="wb") as local_file:
                local_file.write(smb_file.read())
                print(f"Saved file at{local_dir /  file['file_name']}")
                
    else:
        print(f"{file['file_name']} exists. Skipping!")
    print(f"Relative URL: /static/{file['file_name']}")


