
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"
$PSCP = "pscp.exe"

# 1. Upload
Write-Host "Uploading migration script..."
& $PSCP -batch -P 22 -pw $VPS_PASS "c:\Users\hp\OneDrive\Desktop\DICE-main\update_schema_manufacturing.py" "${VPS_USER}@${VPS_IP}:/var/www/dice/"

# 2. Exec
Write-Host "Running migration..."
$cmd = "cd /var/www/dice && source venv/bin/activate && python3 update_schema_manufacturing.py"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP $cmd

# 3. Restart
Write-Host "Restarting dice service..."
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP "supervisorctl restart dice"

Write-Host "Done!"
