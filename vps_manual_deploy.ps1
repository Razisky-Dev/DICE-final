$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

Write-Host "Connecting to VPS $VPS_IP..." -ForegroundColor Cyan

$remoteScript = @"
    set -e
    echo "Starting Deployment on VPS..."
    cd /var/www/dice
    
    echo "Pulling latest changes..."
    git pull origin main
    
    echo "Activating venv and installing requirements..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "Running Migrations..."
    python update_schema_manufacturing.py
    python update_schema_txn_details.py
    
    echo "Restarting Services..."
    supervisorctl restart dice
    systemctl restart nginx
    
    echo "DEPLOYMENT_SUCCESS"
"@

echo $remoteScript | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cat > /tmp/deploy_manual.sh && bash /tmp/deploy_manual.sh"
