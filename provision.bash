#!/bin/bash
set -euo pipefail

APP_DIR="/srv/app/"
BASH_FILE="/home/vagrant/.profile"
VIRTUAL_ENV_DIR="/srv/virtualenv/"
VIRTUAL_ENV_SOURCE="/srv/virtualenv/bin/activate"

sudo apt update
sudo apt install python3-venv nginx -y

(
sudo cat <<'CONFIG'
  upstream app_server {
    server 127.0.0.1:5000;
  }

  server {
    listen 80;
    server_name spotify-analyze.vm;

      location / {
          proxy_pass http://app_server;
      }
  }
CONFIG
) > /etc/nginx/conf.d/nginx.conf

sudo systemctl restart nginx

sudo python3 -m venv "$VIRTUAL_ENV_DIR"

source "$VIRTUAL_ENV_SOURCE"
cd "$APP_DIR"
pip install -r requirements.txt

sudo ufw allow "Nginx Full"
sudo ufw allow ssh
sudo ufw --force enable

if ! grep -qse "### BEGIN Vagrant MANAGED SECTION" "$BASH_FILE"; then
  {
  echo "### BEGIN Vagrant MANAGED SECTION"
  echo ". $VIRTUAL_ENV_SOURCE"
  echo "cd $APP_DIR"
  echo "### END Vagrant MANAGED SECTION"
  } >> "$BASH_FILE"
fi
