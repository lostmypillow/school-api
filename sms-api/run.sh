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
sudo apt-get install -y python3-venv python3-pip wget curl gnupg nginx >/dev/null

curl -sSL -O https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb

# Install the driver
sudo apt-get update -y >/dev/null
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 >/dev/null
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18 >/dev/null
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
sudo apt-get install -y unixodbc-dev >/dev/null
echo "ok"

echo "SETUP [Ensure virtual environment is enabled]"
if [ ! -d "$APP_DIR/.venv" ]; then
    python3 -m venv "$APP_DIR/.venv" >/dev/null
fi
source "$APP_DIR/.venv/bin/activate"
echo "ok"

echo "SETUP [Install Python requirements]"
pip install -r "$APP_DIR/requirements.txt" >/dev/null
pip install gunicorn
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
ExecStart=$APP_DIR/.venv/bin/gunicorn --bind 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker main:app
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL



echo "SETUP [Configure Nginx as a reverse proxy]"
NGINX_CONFIG="/etc/nginx/sites-available/$SERVICE_NAME"
sudo bash -c "cat > $NGINX_CONFIG" <<EOL
server {
    listen 80;

    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
sudo ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/
sudo nginx -t
sudo mkdir -p /etc/systemd/system/nginx.service.d
sudo bash -c "cat > /etc/systemd/system/nginx.service.d/override.conf" <<EOL
[Service]
ExecStartPost=/bin/sleep 0.1
EOL
sudo systemctl daemon-reload
sudo systemctl restart nginx
echo "ok"


echo "RUN [Starting FastAPI systemd service...]"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
if [[ "$(sudo systemctl status $SERVICE_NAME --no-pager --quiet)" == *"active (running)"* ]]; then
    echo "ok"
else
    echo "$SERVICE_NAME failed to start."
    exit 1
fi


echo "[DONE!] Access SMS API at http://$(hostname -I | awk '{print $1}')"

exit 0