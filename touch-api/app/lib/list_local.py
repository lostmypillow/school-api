
import os
from pathlib import Path
local_dir = Path(__file__).resolve().parent.parent.parent / "static"

def list_local():
    return [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
