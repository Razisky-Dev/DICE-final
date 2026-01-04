
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# 1. Find DB files
echo "Finding DB files..."
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "find /var/www/dice -name '*.db'"

# 2. Get readable error log (grep for Error)
echo "Recent Errors:"
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "grep -C 5 'Error' /var/log/dice_err.log | tail -n 20"
