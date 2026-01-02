#!/bin/bash
cd /var/www/dice

# Setup Virtual Env
if [ ! -d venv ]; then python3 -m venv venv; fi
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Run Database Migrations
python3 update_schema_timestamp.py

# Setup Gunicorn Service
cp vps_config/dice.service /etc/systemd/system/dice.service
systemctl daemon-reload
systemctl enable dice
systemctl restart dice

# Setup Nginx
cp vps_config/dice_nginx /etc/nginx/sites-available/dice
ln -sf /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
