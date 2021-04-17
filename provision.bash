#!/bin/bash
set -euo pipefail

APP_DIR="/srv/app/"
BASH_FILE="/home/vagrant/.profile"
VIRTUAL_ENV_DIR="/srv/virtualenv/"
VIRTUAL_ENV_SOURCE="/srv/virtualenv/bin/activate"

sudo apt-get update
sudo apt-get install python3-venv nginx -y

sudo cp /srv/app/nginx.conf /etc/nginx/conf.d/nginx.conf
sudo systemctl restart nginx

chown vagrant:vagrant /srv/

su vagrant <<EOUS
python3 -m venv "$VIRTUAL_ENV_DIR"
source "$VIRTUAL_ENV_SOURCE"
cd "$APP_DIR"
pip install --upgrade pip
pip install -r requirements.txt
EOUS

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
