
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"
$PSCP = "pscp.exe"

Write-Host "Force deploying files to $VPS_IP..." -ForegroundColor Cyan

# 1. Upload app.py
Write-Host "Uploading app.py..."
& $PSCP -batch -P 22 -pw $VPS_PASS "c:\Users\hp\OneDrive\Desktop\DICE-main\app.py" "${VPS_USER}@${VPS_IP}:/var/www/dice/"

# 2. Upload templates
Write-Host "Uploading pricing.html..."
& $PSCP -batch -P 22 -pw $VPS_PASS "c:\Users\hp\OneDrive\Desktop\DICE-main\templates\admin\pricing.html" "${VPS_USER}@${VPS_IP}:/var/www/dice/templates/admin/"

Write-Host "Uploading orders.html..."
& $PSCP -batch -P 22 -pw $VPS_PASS "c:\Users\hp\OneDrive\Desktop\DICE-main\templates\admin\orders.html" "${VPS_USER}@${VPS_IP}:/var/www/dice/templates/admin/"

# 3. Restart Supervisor
Write-Host "Restarting application..."
$cmd = "supervisorctl restart dice_app"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP $cmd

Write-Host "Force deployment complete!" -ForegroundColor Green
