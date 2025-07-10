#!/bin/bash

set -e

if ! sudo -v >/dev/null 2>&1; then
  echo "Error: this script requires sudo privileges."
  exit 1
fi

APP_NAME="predictionRMN"
APP_DIR="/opt/$APP_NAME"
FRONT_STATIC_DIR="/var/www/$APP_NAME"
SYSTEMD_SERVICE="/etc/systemd/system/$APP_NAME.service"
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
NGINX_ENABLED="/etc/nginx/sites-enabled/$APP_NAME"

REMOVE_PACKAGES=false
if [[ "$1" == "--remove-packages" ]]; then
  REMOVE_PACKAGES=true
fi

echo "==> Stopping and disabling systemd service"
sudo systemctl stop "$APP_NAME" || true
sudo systemctl disable "$APP_NAME" || true
sudo rm -f "$SYSTEMD_SERVICE"
sudo systemctl daemon-reload

echo "==> Removing Nginx files"
sudo rm -f "$NGINX_CONF"
sudo rm -f "$NGINX_ENABLED"

echo "==> Reloading Nginx"
sudo nginx -t && sudo systemctl reload nginx

echo "==> Removing application directories"
sudo rm -rf "$APP_DIR"
sudo rm -rf "$FRONT_STATIC_DIR"

if $REMOVE_PACKAGES; then
  echo "==> Uninstalling apt packages"
  sudo apt purge -y python3 python3-pip python3-venv nginx git
  sudo apt autoremove -y
else
  echo "==> Apt packages kept (to uninstall, rerun with --remove-packages)"
fi

echo "==> Uninstallation completed."
