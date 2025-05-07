set -eo pipefail
trap 'echo "[!] ERROR at line $LINENO: $BASH_COMMAND exited with status $?"' ERR
APP_DIR="$(pwd)/backend"
SERVICE_NAME=""
PORT="8005"

VERSION=$(python3 sync_version.py)
echo "KwVM API DEPLOY SCRIPT FOR v$VERSION STARTING..."
echo ""

BACKEND_ENV_FILE="$APP_DIR/src/config.py"
BACKEND_ENV_EXAMPLE="$APP_DIR/src/config.py.example"

if [ ! -f "$BACKEND_ENV_FILE" ]; then
    echo "SETUP [Creating backend config.py file...]"
    cp "$BACKEND_ENV_EXAMPLE" "$BACKEND_ENV_FILE"
    nano "$BACKEND_ENV_FILE"
    echo "Done! Backend config.py created at $BACKEND_ENV_FILE"
    echo ""
fi
# FRONTEND_ENV_FILE="$(pwd)/frontend/.env"
# FRONTEND_ENV_EXAMPLE="$(pwd)/frontend/.env.example"

# if [ ! -f "$FRONTEND_ENV_FILE" ]; then
#     echo "SETUP [Creating frontend .env file...]"
#     cp "$FRONTEND_ENV_EXAMPLE" "$FRONTEND_ENV_FILE"
#     nano "$FRONTEND_ENV_FILE"
#     echo "Done! Frontend .env created at $FRONTEND_ENV_FILE"
#     echo ""
# fi

echo "FRONTEND [(Re)building frontend...]"
FRONTEND_DIR="$(pwd)/frontend"
PUBLIC_DIR="$(pwd)/backend/public"

if [ -d "$PUBLIC_DIR" ]; then
    rm -rf "$PUBLIC_DIR"
fi

mkdir -p "$PUBLIC_DIR"
cd "$FRONTEND_DIR"
rm -rf node_modules
rm -f package-lock.json
npm install >/dev/null 2>&1
npm run build >/dev/null 2>&1

cd ..
echo "Done."
echo ""

echo "SETUP [Updating system...]"
sudo apt-get update -y >/dev/null
echo "ok"
echo ""

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
echo ""

echo "SETUP [Enabling virtual environment...]"
if [ ! -d "$APP_DIR/.venv" ]; then
    python3 -m venv "$APP_DIR/.venv" >/dev/null
fi
source "$APP_DIR/.venv/bin/activate"
echo "ok"
echo ""

echo "SETUP [Installing Python requirements...]"
pip install -r "$APP_DIR/requirements.txt" >/dev/null
# Gunicorn is installed only in deployment. This is becuz gunicorn doesn't work in Windows, where most of the dev work happens
pip install gunicorn >/dev/null
echo "ok"
echo ""

echo "SETUP [Registering as systemd service and starting the service...]"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=KwVM
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/gunicorn --bind 0.0.0.0:$PORT -k uvicorn.workers.UvicornWorker src.main:app
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment="TZ=Asia/Taipei"

[Install]
WantedBy=multi-user.target
EOL
echo "ok"
echo ""

echo "RUN [Starting FastAPI systemd service...]"
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME
if [[ "$(sudo systemctl status $SERVICE_NAME --no-pager --quiet)" == *"active (running)"* ]]; then
    echo "ok"
    echo ""
else
    echo "$SERVICE_NAME failed to start."
    echo ""
    exit 1
fi


echo "DONE [Access KwVM API at http://$(hostname -I | awk '{print $1}'):$PORT]"

exit 0