
# Validating directory
if [ ! -d "/var/www/dice" ]; then
    mkdir -p /var/www/dice
    git clone https://github.com/Razisky-Dev/DICE-final.git /var/www/dice
fi

cd /var/www/dice
git reset --hard
git pull origin main

# Venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install
pip install -r requirements.txt
pip install gunicorn

# DB
python3 init_db.py
python3 migrate_all.py

# Fix Admin (Assumes file is copied)
if [ -f "fix_admin_login_final.py" ]; then
    echo "Running Admin Fix..."
    python3 fix_admin_login_final.py
    rm fix_admin_login_final.py
else
    echo "WARNING: fix_admin_login_final.py not found!"
fi

# Supervisor
cat > /etc/supervisor/conf.d/dice.conf << 'EOF'
[program:dice]
command=/var/www/dice/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=/var/www/dice
user=root
autostart=true
autorestart=true
stdout_logfile=/var/log/dice.log
stderr_logfile=/var/log/dice_err.log
EOF

# Nginx
cat > /etc/nginx/sites-available/dice << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Restart
supervisorctl reread
supervisorctl update
supervisorctl restart dice
systemctl restart nginx

echo "Deployment Complete."
