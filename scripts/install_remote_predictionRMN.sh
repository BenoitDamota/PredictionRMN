#!/bin/bash

set -e

if ! sudo -v >/dev/null 2>&1; then
  echo "Error: this script requires sudo privileges."
  exit 1
fi

APP_NAME="predictionRMN"
GIT_REPO="https://github.com/BenoitDamota/PredictionRMN.git"
APP_DIR="/opt/$APP_NAME"
FRONT_STATIC_DIR="/var/www/$APP_NAME"
SYSTEMD_SERVICE="/etc/systemd/system/$APP_NAME.service"
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
USER="webadmin"
ENV_API_PATH="/nmr"

echo "==> Updating packages"
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx git

echo "==> Creating application folder"
sudo mkdir -p "$APP_DIR"
sudo chown "$USER":"$USER" "$APP_DIR"

cd "$APP_DIR"
echo "==> Cloning repository"
git clone "$GIT_REPO" .

echo "==> Creating virtual environment"
python3 -m venv venv
source venv/bin/activate

echo "==> Installing Python dependencies"
pip install --upgrade pip
pip install -r backend/remote-requirements-lock.txt

echo "==> Creating static frontend folder"
sudo mkdir -p "$FRONT_STATIC_DIR"
sudo chown "$USER":"$USER" "$FRONT_STATIC_DIR"

echo "==> Copying React build"
cp -r frontend/build/* "$FRONT_STATIC_DIR/"

echo "==> Creating frontend environment file"
sudo tee "$FRONT_STATIC_DIR/env-config.js" > /dev/null <<EOF
window._env_ = {
  EXTERNAL_ENV_API_PATH: "$ENV_API_PATH"
};
EOF

echo "==> Configuring Nginx"
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    root $FRONT_STATIC_DIR;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:52586/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF


echo "==> Activating Nginx configuration"
sudo unlink /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "==> Creating systemd service for Gunicorn"
sudo tee "$SYSTEMD_SERVICE" > /dev/null <<EOF
[Unit]
Description=Gunicorn for $APP_NAME Flask backend
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:52586 remote:app

[Install]
WantedBy=multi-user.target
EOF

echo "==> Starting service"
sudo systemctl daemon-reexec
sudo systemctl enable "$APP_NAME"
sudo systemctl restart "$APP_NAME"

echo "==> Deployment completed!"
echo "Application accessible at: https://quchempedia.univ-angers.fr/nmr/"