$VPS_IP = "72.62.150.44"
$USER = "root"
$REPO_URL = "https://github.com/Razisky-Dev/DICE-final.git"
$APP_DIR = "/var/www/dice"

Write-Host "Deploying to $USER@$VPS_IP..." -ForegroundColor Cyan

# 1. SSH into VPS to prepare directories and install git if missing
Write-Host "Preparing remote environment..." -ForegroundColor Yellow
ssh $USER@$VPS_IP "
    apt-get update && apt-get install -y git python3-pip python3-venv nginx
    mkdir -p $APP_DIR
"

# 2. Clone or Pull the repository
Write-Host "Updating codebase..." -ForegroundColor Yellow
ssh $USER@$VPS_IP "
    if [ ! -d $APP_DIR/.git ]; then
        git clone $REPO_URL $APP_DIR
    else
        cd $APP_DIR
        git remote set-url origin $REPO_URL
        git pull origin main
    fi
"

# 3. Upload vps_config files (in case they changed locally)
Write-Host "Uploading configuration files..." -ForegroundColor Yellow
scp -r ./vps_config "${USER}@${VPS_IP}:${APP_DIR}/"

# 4. Setup and Restart Services
Write-Host "Configuring and restarting services..." -ForegroundColor Yellow
ssh $USER@$VPS_IP "
    cd $APP_DIR
    
    # Setup Virtual Env
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
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
"

Write-Host "Deployment Complete! Visit http://$VPS_IP to verify." -ForegroundColor Green
