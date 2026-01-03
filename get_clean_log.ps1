
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"

# 1. Clear log
Write-Host "Clearing log..."
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP "truncate -s 0 /var/log/dice_err.log"

# 2. Restart and Curl
Write-Host "Restarting and triggering error..."
$cmd = "supervisorctl restart dice && sleep 5 && curl -v http://127.0.0.1:8000/admin/pricing"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP $cmd

# 3. Read log
Write-Host "Reading log..."
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP "cat /var/log/dice_err.log"
