
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# 1. Prepare Log on Server
echo "Preparing log..."
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "tail -n 200 /var/log/dice_err.log > /var/www/dice/debug_err.log"

# 2. Download Log
echo "Downloading log..."
echo y | pscp.exe -batch -pw $VPS_PASS $VPS_USER@$VPS_IP`:/var/www/dice/debug_err.log debug_err.log

# 3. Clean up
echo "Cleaning up..."
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "rm /var/www/dice/debug_err.log"
