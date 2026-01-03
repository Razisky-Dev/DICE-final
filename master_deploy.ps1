# Master Deploy Script
# 1. Commits and Pushes changes
# 2. Deploys to Hostinger VPS
# 3. Runs Schema Updates
# 4. Restarts Services

$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$REPO_URL = "https://github.com/Razisky-Dev/DICE-final.git"

# 1. Git Operations
Write-Host "Step 1: Mastering Code (Git Commit & Push)..." -ForegroundColor Cyan
git add .
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "Master Deploy: $timestamp - Fix 500 error and referencing updates"
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Git push failed or nothing to push. Continuing to deployment anyway..."
}

# 2. VPS Operations
Write-Host "Step 2: Connecting to VPS ($VPS_IP)..." -ForegroundColor Cyan

# Command to run on VPS
$remoteScript = @"
    # Stop on error
    set -e
    
    echo "Files listing for diagnostics:"
    ls -la /var/www/dice

    echo "Navigating to app directory..."
    cd /var/www/dice

    echo "Pulling latest changes..."
    # Reset to ensure we can pull clean if needed, or just pull. 
    # Safety: Stash changes if any (e.g. local .env changes on server)
    git stash
    git pull origin main
    git stash pop || true # Restore config if any, ignore conflict if none

    echo "Activating virtual environment..."
    source venv/bin/activate

    echo "Installing requirements..."
    pip install -r requirements.txt

    echo "Running Schema Updates..."
    # Run the manufacturing price fix
    if [ -f "update_schema_manufacturing.py" ]; then
        echo "Running update_schema_manufacturing.py..."
        python update_schema_manufacturing.py
    else
        echo "Warning: update_schema_manufacturing.py not found!"
    fi

    # Run the transaction details fix
    if [ -f "update_schema_txn_details.py" ]; then
        echo "Running update_schema_txn_details.py..."
        python update_schema_txn_details.py
    else
         echo "Warning: update_schema_txn_details.py not found!"
    fi
    
    # Run dealer price schema update just in case
    if [ -f "update_schema_dealer_price.py" ]; then
        echo "Running update_schema_dealer_price.py..."
        python update_schema_dealer_price.py
    fi

    echo "Restarting Services..."
    supervisorctl restart dice
    systemctl restart nginx

    echo "Deployment Complete!"
"@

# Execute remote command using plink
# Note: Using echo to pipe script to bash explicitly to avoid complex escaping
$command = "echo '$remoteScript' > /tmp/deploy_script.sh && bash /tmp/deploy_script.sh"

# Using plink directly with the script block
# We need to be careful with quotes in powershell passing to plink passing to bash
# Simpler approach: Pass the commands directly? Or Use a Here-String for plink input?
# Plink can accept commands from stdin with -m, or file.
# We will use the input redirection.

# Write remote script to local temp file to avoid quoting hell, then upload? No, scp needed.
# Let's just feed it via standard input to plink is risky if not interactive.
# Best: Pass the script as an argument to bash -s

$scriptBlock = {
    param($ip, $user, $pass, $script)
    echo $script | plink.exe -batch -ssh $user@$ip -pw $pass "cat > /tmp/deploy_script.sh && bash /tmp/deploy_script.sh"
}

# Invoke the plink command
echo $remoteScript | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cat > /tmp/deploy_script.sh && bash /tmp/deploy_script.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Master Deployment Successful!" -ForegroundColor Green
    Write-Host "Please verify at http://$VPS_IP/admin/pricing" -ForegroundColor Yellow
} else {
    Write-Error "Deployment script failed on VPS."
}
