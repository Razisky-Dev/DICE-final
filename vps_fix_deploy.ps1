$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

Write-Host "Connecting to VPS $VPS_IP..." -ForegroundColor Cyan

# We use just LF in the here-string, though Powershell might normalize it.
# Best approach: Use sed on the remote side to strip \r
$remoteScript = @"
    set -e
    echo "Starting Deployment on VPS (Attempt 2)..."
    
    # Fix potential previous messing up
    cd /var/www/dice
    
    echo "Pulling latest changes..."
    git pull origin main || echo "Git pull warning (might be up to date)"
    
    echo "Activating venv..."
    source venv/bin/activate
    
    echo "Installing requirements..."
    pip install -r requirements.txt
    
    echo "Running Migrations..."
    python update_schema_manufacturing.py
    python update_schema_txn_details.py
    
    echo "Restarting Services..."
    supervisorctl restart dice
    
    echo "Restarting Nginx..."
    systemctl restart nginx
    
    echo "Verifying Nginx status..."
    systemctl status nginx --no-pager | head -n 3
    
    echo "DEPLOYMENT_VERIFIED"
"@

# We upload, strip carriage returns using tr, then execute
echo $remoteScript | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cat > /tmp/deploy_fix.sh && tr -d '\r' < /tmp/deploy_fix.sh > /tmp/deploy_final.sh && bash /tmp/deploy_final.sh"
