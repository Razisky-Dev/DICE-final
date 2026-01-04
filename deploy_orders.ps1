
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Copy Files
echo y | pscp.exe -batch -pw $VPS_PASS templates/orders.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/orders.html

# Restart
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "supervisorctl restart dice"
