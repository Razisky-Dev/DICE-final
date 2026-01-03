
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"
$PSCP = "pscp.exe"

# 1. Upload
Write-Host "Uploading check script..."
& $PSCP -batch -P 22 -pw $VPS_PASS "c:\Users\hp\OneDrive\Desktop\DICE-main\check_db_status.py" "${VPS_USER}@${VPS_IP}:/var/www/dice/"

# 2. Run
Write-Host "Running check script..."
$cmd = "cd /var/www/dice && source venv/bin/activate && python3 check_db_status.py"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP $cmd
