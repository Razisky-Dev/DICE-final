#!/bin/bash
set -e

# Configuration
DB_NAME="dice_db"
DB_USER="dice_user"
DB_PASS="StrongPass123!" # Change this!
APP_DIR="/var/www/dice"
REPO_URL="https://github.com/Razisky-Dev/DICE-final.git"

# 1. Update System
echo "Updating system..."
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv git nginx supervisor mariadb-server curl ufw

# 2. Setup Database
echo "Setting up MariaDB..."
service mariadb start

# Secure installation (programmatic)
# Note: On fresh installs, root has no password or uses socket auth. 
# We'll just create our user safely.
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# 3. Clone/Update Repo
echo "Setting up application..."
mkdir -p $APP_DIR
if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR
    git pull origin main
else
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# 4. Setup Python Environment
echo "Setting up Virtualenv..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn pymysql cryptography

# 5. Create .env
echo "Creating .env..."
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
SQLALCHEMY_DATABASE_URI=mysql+pymysql://$DB_USER:$DB_PASS@localhost/$DB_NAME
MAIL_USERNAME=admin@razilhub.com
MAIL_PASSWORD=admin123
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
EOF

# 6. Initialize DB
echo "Initializing Database..."
export FLASK_APP=app.py
# If init_db.py exists and works, use it, otherwise use flask command
if [ -f "init_db.py" ]; then
    python init_db.py
else
    flask db upgrade
fi

# 7. Setup Supervisor
echo "Configuring Supervisor..."
cat > /etc/supervisor/conf.d/dice.conf << EOF
[program:dice]
command=$APP_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=$APP_DIR
user=root
autostart=true
autorestart=true
stdout_logfile=/var/log/dice.log
stderr_logfile=/var/log/dice_err.log
environment=PATH="$APP_DIR/venv/bin",FLASK_APP="app.py"
EOF

# 8. Setup Nginx
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/dice << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 9. Firewall
echo "Configuring Firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
# ufw --force enable # Be careful with this on remote servers!

# 10. Restart Services
echo "Restarting services..."
supervisorctl reread
supervisorctl update
supervisorctl restart dice
systemctl restart nginx

echo "Setup Complete! Access your app at http://$(curl -s ifconfig.me)"
