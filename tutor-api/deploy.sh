#!/bin/bash

# Exit on error
set -e
APP_DIR="$(pwd)"
SERVICE_NAME="kwtutor"
PORT="8001"
VERSION=$(python3 get_version.py)


echo "[*]  v$VERSION starting deployment..."
echo ""

if [ ! -f "$(pwd)/src/config.py" ]; then
    cp "$(pwd)/src/config.py.example" "$(pwd)/src/config.py" 
    echo "[✓] No backend config.py found, created at $(pwd)/src/config.py"
    echo ""
fi


echo "[*] Checking backend config.py..."
nano "$(pwd)/src/config.py"
echo ""


chmod o+x "$APP_DIR"
echo "[✓] ok"
echo ""

echo "[*] Enabling virtual environment..."
cd "$APP_DIR"
uv sync
echo "[✓] ok"
echo ""

echo "[*] Registering as systemd service and starting the service..."
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/gunicorn --bind 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker src.main:app
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment=TZ=Asia/Taipei

[Install]
WantedBy=multi-user.target
EOL
echo "[✓] ok"
echo ""

echo "[*] Starting FastAPI systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME
if [[ "$(sudo systemctl status $SERVICE_NAME --no-pager --quiet)" == *"active (running)"* ]]; then
    echo "[✓] ok"
    echo ""
else
    echo "[x] $SERVICE_NAME failed to start."
    echo ""
    exit 1
fi

echo "[✓] Access  at http://$(hostname -I | awk '{print $1}')/api/tutor/docs"

exit 0