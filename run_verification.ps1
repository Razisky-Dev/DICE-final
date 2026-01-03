
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"
$PSCP = "pscp.exe"

# 1. Upload
Write-Host "Uploading verify script..."
& $PSCP -batch -P 22 -pw $VPS_PASS "c:\Users\hp\OneDrive\Desktop\DICE-main\verify_schema.py" "${VPS_USER}@${VPS_IP}:/var/www/dice/"

# 2. Run
Write-Host "Running verify..."
$cmd = "cd /var/www/dice && source venv/bin/activate && python3 verify_schema.py"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP $cmd

# 3. Download result
Write-Host "Downloading result..."
& $PSCP -batch -pw $VPS_PASS "${VPS_USER}@${VPS_IP}:/var/www/dice/schema_verification.txt" "c:\Users\hp\OneDrive\Desktop\DICE-main\schema_verification.txt"

Write-Host "Done!"
