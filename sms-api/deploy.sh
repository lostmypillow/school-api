#!/bin/bash

# Exit on error
set -e
APP_DIR="$(pwd)"
SERVICE_NAME=""
PORT="8003"
BACKEND_CONFIG="$APP_DIR/src/config.py"
BACKEND_CONFIG_EXAMPLE="$APP_DIR/src/config.py.example"
VERSION=$(python3 get_version.py)


echo "[*] $SERVICE_NAME v$VERSION starting deployment..."
echo ""

if [ ! -f "$BACKEND_CONFIG" ]; then
    cp "$BACKEND_CONFIG_EXAMPLE" "$BACKEND_CONFIG" 
    echo "[✓] No backend config.py found, created at $BACKEND_CONFIG"
    echo ""
fi

echo "[*] Checking backend config.py..."
nano "$BACKEND_CONFIG"
echo ""


UPDATE_STAMP="$HOME/.cache/last-apt-update"
mkdir -p "$(dirname "$UPDATE_STAMP")"

MAX_AGE=3600

if [ ! -f "$UPDATE_STAMP" ] || [ $(( $(date +%s) - $(stat -c %Y "$UPDATE_STAMP") )) -ge $MAX_AGE ]; then
    echo "[*] Running apt-get update..."
    sudo apt-get update && touch "$UPDATE_STAMP"
else
    echo "[✓] apt-get update was run recently, skipping."
fi
echo ""

echo "[*] Ensuring necessary packages are installed..."
install_if_missing() {
    for pkg in "$@"; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            echo "Installing $pkg..."
            sudo apt-get install -y "$pkg" >/dev/null
        else
            echo "$pkg is already installed."
        fi
    done
}

# Install core utilities
install_if_missing python3-venv python3-pip wget curl gnupg nginx

# Add Microsoft repository if not already present
if ! grep -q "packages.microsoft.com" /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null; then
    curl -sSL -O https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb
    sudo dpkg -i packages-microsoft-prod.deb >/dev/null
    rm packages-microsoft-prod.deb
    sudo apt-get update -y >/dev/null
fi

# Install Microsoft SQL tools with license acceptance
install_if_missing msodbcsql18
install_if_missing mssql-tools18
install_if_missing unixodbc-dev

# Add to PATH if not already present
if ! grep -q 'mssql-tools18/bin' ~/.bashrc; then
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
    source ~/.bashrc
fi

chmod o+x "$(pwd)"
chmod o+x "$HOME"
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
Description=$SERVICE_NAME
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

echo "[✓] Access $SERVICE_NAME API at http://$(hostname -I | awk '{print $1}'):$PORT"

exit 0