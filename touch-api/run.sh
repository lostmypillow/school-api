#!/bin/bash

# Exit on error
set -e
APP_DIR="$(pwd)"
SERVICE_NAME="touchscreen"
PORT="8002"


echo "SETUP [Updating system...]"
sudo apt-get update -y >/dev/null
echo "ok"

echo "SETUP [Ensuring necessary packages are installed...]"
sudo apt-get install -y python3-venv python3-pip wget curl gnupg nginx >/dev/null
curl -sSL -O https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb >/dev/null
rm packages-microsoft-prod.deb >/dev/null
sudo apt-get update -y >/dev/null
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 >/dev/null
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18 >/dev/null
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
sudo apt-get install -y unixodbc-dev >/dev/null
echo "ok"

echo "SETUP [Enabling virtual environment...]"
if [ ! -d "$APP_DIR/.venv" ]; then
    python3 -m venv "$APP_DIR/.venv" >/dev/null
fi
source "$APP_DIR/.venv/bin/activate"
echo "ok"

echo "SETUP [Installing Python requirements...]"
pip install -r "$APP_DIR/requirements.txt" >/dev/null
# Gunicorn is installed only in deployment. This is becuz gunicorn doesn't work in Windows, where most of the dev work happens
pip install gunicorn >/dev/null
echo "ok"

echo "SETUP [Registering as systemd service and starting the service...]"
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

[Install]
WantedBy=multi-user.target
EOL
echo "ok"

echo "RUN [Starting FastAPI systemd service...]"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME
if [[ "$(sudo systemctl status $SERVICE_NAME --no-pager --quiet)" == *"active (running)"* ]]; then
    echo "ok"
else
    echo "$SERVICE_NAME failed to start."
    exit 1
fi


echo "[DONE!] Access  API at http://$(hostname -I | awk '{print $1}'):$PORT"

exit 0