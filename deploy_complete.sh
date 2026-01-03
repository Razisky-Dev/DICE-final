#!/bin/bash
set -e  # Exit on any error

VPS_IP="72.62.150.44"
APP_DIR="/var/www/dice"
REPO_URL="https://github.com/Razisky-Dev/DICE-final.git"

# DB Config
DB_NAME="dice_db"
DB_USER="dice_user"
DB_PASS="dice_pass_secure_123" # In prod, use random or prompt, but hardcoded for reliability here

echo "=========================================="
echo "DICE Application Deployment Script (MySQL Edition)"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "Installing required packages (incl. MariaDB)..."
apt install -y python3 python3-pip python3-venv git nginx systemd curl mariadb-server pkg-config libmysqlclient-dev

# Start MariaDB
systemctl start mariadb
systemctl enable mariadb

# Setup Database
echo "Configuring MariaDB..."
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Create application directory
echo "Setting up application directory..."
mkdir -p $APP_DIR

# Clone or update repository
if [ -d "$APP_DIR/.git" ]; then
    echo "Repository exists, pulling latest changes..."
    cd $APP_DIR
    git fetch origin
    git reset --hard origin/main || git pull origin main
elif [ -d "$APP_DIR" ] && [ "$(ls -A $APP_DIR)" ]; then
    echo "Directory exists but is not a git repository. Backing up and cloning fresh..."
    mv $APP_DIR ${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)
    git clone $REPO_URL $APP_DIR
else
    echo "Cloning repository..."
    git clone $REPO_URL $APP_DIR
fi

cd $APP_DIR

# Create virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn pymysql cryptography

# Setup environment variables if .env doesn't exist (re-create to ensure DB URI is correct)
# Or strictly check if we need to update it. 
# For safety, let's backup existing .env and recreate to ensure MariaDB usage.
if [ -f ".env" ]; then
    echo "Backing up existing .env..."
    cp .env .env.bak
fi

echo "Creating/Updating .env file..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
{
    echo "SECRET_KEY=$SECRET_KEY"
    echo "SQLALCHEMY_DATABASE_URI=mysql+pymysql://$DB_USER:$DB_PASS@localhost/$DB_NAME"
    echo "MAIL_USERNAME=admin@razilhub.com"
    echo "MAIL_PASSWORD=admin123"
    echo "MAIL_SERVER=smtp.gmail.com"
    echo "MAIL_PORT=587"
    echo "MAIL_USE_TLS=True"
    # Paystack Keys (Set manually on server or via .env.local)
    # echo "PAYSTACK_SECRET_KEY=ReplaceWithLiveSecretKey"
    # echo "PAYSTACK_PUBLIC_KEY=ReplaceWithLivePublicKey"
    echo "SITE_NAME=RazilHub"
} > .env
echo ".env file updated (Paystack keys preserved if existing, or set manually)."

# Create necessary directories
mkdir -p instance
mkdir -p static/css
mkdir -p templates

# Initialize database
echo "Initializing database..."
python3 init_db.py

# Run any database migrations
if [ -f "update_schema_timestamp.py" ]; then
    echo "Running database migrations..."
    python3 update_schema_timestamp.py || true
fi

# Setup Gunicorn systemd service
echo "Setting up Gunicorn service..."
# Ensure vps_config exists or create it temporarily if missing in repo (it should be there)
if [ ! -f "vps_config/dice.service" ]; then
    mkdir -p vps_config
    # Create service file content dynamically if missing
    cat > vps_config/dice.service <<EOF
[Unit]
Description=Gunicorn instance to serve DICE
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:dice.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
EOF
fi

cp vps_config/dice.service /etc/systemd/system/dice.service
systemctl daemon-reload
systemctl enable dice
systemctl restart dice

# Setup Nginx (Dynamic Create if missing)
echo "Configuring Nginx..."
if [ ! -f "vps_config/dice_nginx" ]; then
    mkdir -p vps_config
    cat > vps_config/dice_nginx <<EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/dice.sock;
    }
}
EOF
fi

cp vps_config/dice_nginx /etc/nginx/sites-available/dice
ln -sf /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx

# Check service status
echo "Checking service status..."
systemctl status dice --no-pager -l || true

echo ""
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo "Application URL: http://$VPS_IP"
echo ""
