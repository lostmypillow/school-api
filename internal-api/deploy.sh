#!/bin/bash

# Exit on error
set -e
SERVICE_NAME="ldap"
PORT="8008"
VERSION=$(python3 get_version.py)

echo "[*] $SERVICE_NAME v$VERSION starting deployment..."
echo ""

e
echo "[*] Creating virtual environment with uv..."
uv sync
echo "[✓] ok"
echo ""

echo "[*] Registering as systemd service..."
chmod o+x "$(pwd)"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=$SERVICE_NAME
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/.venv/bin/fastapi run --port $PORT --workers 2
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment=TZ=Asia/Taipei

[Install]
WantedBy=multi-user.target
EOL
echo "[✓] ok"
echo ""

echo "[*] Reloading systemd and starting $SERVICE_NAME..."

sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "[✓] $SERVICE_NAME is running."
    echo ""
else
    echo "[x] $SERVICE_NAME failed to start."
    echo ""
    sudo systemctl status "$SERVICE_NAME" --no-pager
    exit 1
fi

echo "[✓] Access $SERVICE_NAME at https:///api/ldap/docs"

exit 0
