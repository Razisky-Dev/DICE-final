$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

Write-Host "Connecting to VPS $VPS_IP for FORCE DEPLOY..." -ForegroundColor Red

$remoteScript = @"
    set -e
    echo "--- FORCE DEPLOY START ---"
    cd /var/www/dice
    
    echo "Resetting Git state..."
    git reset --hard HEAD
    git clean -fd
    
    echo "Pulling latest changes..."
    git pull origin main
    
    echo "Activating venv..."
    source venv/bin/activate
    
    echo "Installing requirements..."
    pip install -r requirements.txt
    
    echo "Running Migrations..."
    # Always run these, they are idempotent-ish (check for column existence)
    python update_schema_manufacturing.py
    python update_schema_txn_details.py
    python update_schema_dealer_price.py
    
    echo "Restarting Services..."
    supervisorctl restart dice
    systemctl restart nginx
    
    echo "DEPLOYMENT_SUCCESS"
    echo "--- FORCE DEPLOY END ---"
"@

echo $remoteScript | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cat > /tmp/force_deploy.sh && tr -d '\r' < /tmp/force_deploy.sh > /tmp/force_deploy_clean.sh && bash /tmp/force_deploy_clean.sh"
