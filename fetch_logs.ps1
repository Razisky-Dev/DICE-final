
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Fetch last 50 lines of error log
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "tail -n 50 /var/log/dice_err.log"
