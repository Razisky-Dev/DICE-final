$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'
$REPO_URL = "https://github.com/Razisky-Dev/DICE-final.git"
$APP_DIR = "/var/www/dice"

# Helper for Plink
function Run-Plink {
    param($cmd)
    Write-Host "Running on VPS: $cmd" -ForegroundColor Gray
    # echo "y" | plink ... is a hack to auto-accept host key if not present, but -batch usually fails if host key unknown.
    # We can try just running it. If host key is not cached, this might fail.
    # A workaround is to auto-accept: -o StrictHostKeyChecking=no equivalent for plink? 
    # Plink doesn't have that easily. 
    # However, since the user has likely connected before (or I can try), let's hope.
    # If not, we might need to manually connect once. 
    # Actually, echo Y | plink ... might work for the first time.
    
    plink -batch -ssh -pw $PASS $USER@$VPS_IP $cmd
}

Write-Host "Deploying to $USER@$VPS_IP using Plink..." -ForegroundColor Cyan

# 1. Prepare
Write-Host "1. Preparing remote environment..." -ForegroundColor Yellow
Run-Plink "apt-get update && apt-get install -y git python3-pip python3-venv nginx; mkdir -p $APP_DIR"

# 2. Git Pull
Write-Host "2. Updating codebase..." -ForegroundColor Yellow
Run-Plink "if [ ! -d $APP_DIR/.git ]; then git clone $REPO_URL $APP_DIR; else cd $APP_DIR; git remote set-url origin $REPO_URL; git fetch origin; git reset --hard origin/main; fi"

# 3. Upload Config using PSCP
Write-Host "3. Uploading configuration files..." -ForegroundColor Yellow
# PSCP recursive copy
# Note: PSCP might need absolute path for source if . is ambiguous, but relative usually works.
# -batch to avoid prompts
pscp -r -batch -pw $PASS ./vps_config ${USER}@${VPS_IP}:${APP_DIR}/

# 4. Restart Services
Write-Host "4. Configuring and restarting services..." -ForegroundColor Yellow
$setup_script = "
    cd $APP_DIR
    
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
"
# Fix CRLF line endings from Windows to Linux
$setup_script = $setup_script -replace "`r`n", "`n"
Run-Plink $setup_script

Write-Host "Deployment Complete! Visit http://$VPS_IP" -ForegroundColor Green
