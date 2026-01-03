
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"

Write-Host "--- dice_err.log ---"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP "tail -n 50 /var/log/dice_err.log"

Write-Host "--- dice.log ---"
& $PLINK -batch -ssh -l $VPS_USER -pw $VPS_PASS -P 22 $VPS_IP "tail -n 50 /var/www/dice/dice.log"
