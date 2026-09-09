import json
import logging
frontend_package = "frontend/package.json"
version_py_path = "backend/src/version.py"

with open(frontend_package, "r") as f:
    package = json.load(f)

version = package.get("version", "0.0.0")

with open(version_py_path, "w") as f:
    f.write(f'# Auto-generated file. Do not edit manually.\nVERSION = "{version}"\n')

logging.info(version)