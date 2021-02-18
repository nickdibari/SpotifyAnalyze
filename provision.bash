#!/bin/bash
set -euo pipefail

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

sudo python3 -m venv /srv/virtualenv

source /srv/virtualenv/bin/activate
cd /srv/app
pip install -r requirements.txt

sudo ufw allow "Nginx Full"
sudo ufw allow ssh
sudo ufw --force enable

BASH_FILE="/home/vagrant/.profile"

if ! grep -qse "### BEGIN dotfiles MANAGED SECTION" "$BASH_FILE"; then
(
cat <<'PROFILE'
   ### BEGIN Vagrant MANAGED SECTION
   . /srv/virtualenv/bin/activate
   cd /srv/app/
   ### END Vagrant MANAGED SECTION
PROFILE
) >> "$BASH_FILE"
fi
