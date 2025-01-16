#!/bin/bash

# Exit on error
set -e
APP_DIR="$(pwd)"
SERVICE_NAME="fastapi"
DISTRO=$(lsb_release -is)


echo "SETUP [Update system]"
sudo apt-get update -y >/dev/null
echo "ok"

echo "SETUP [Ensure necessary packages are installed]"
sudo apt-get install -y python3-venv python3-pip wget curl gnupg >/dev/null

curl -sSL -O https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb
# Install the package
sudo dpkg -i packages-microsoft-prod.deb
# Delete the file
rm packages-microsoft-prod.deb

# Install the driver
sudo apt-get update -y
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
# optional: for bcp and sqlcmd
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
# optional: for unixODBC development headers
sudo apt-get install -y unixodbc-dev
echo "ok"

echo "SETUP [Ensure virtual environment is enabled]"
if [ ! -d "$APP_DIR/.venv" ]; then
    python3 -m venv "$APP_DIR/.venv" >/dev/null
fi
source "$APP_DIR/.venv/bin/activate"
echo "ok"

echo "SETUP [Install Python requirements]"
pip install -r "$APP_DIR/requirements.txt" >/dev/null
echo "ok"

echo "SETUP [Register as systemd service and start it]"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=SMS
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python -m fastapi run $APP_DIR/main.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd, enable, and start the service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

STATUS=$(sudo systemctl status $SERVICE_NAME --no-pager --quiet)
echo "$STATUS"

# Graceful exit if the service is running correctly
if [[ "$STATUS" == *"active (running)"* ]]; then
    echo "$SERVICE_NAME is running successfully."
    exit 0
else
    echo "$SERVICE_NAME failed to start."
    exit 1
fi