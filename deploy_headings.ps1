
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Copy All Modified Templates
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/dashboard.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/dashboard.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/orders.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/orders.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/users.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/users.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/transactions.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/transactions.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/stores.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/stores.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/pricing.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/pricing.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/orders.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/orders.html
echo y | pscp.exe -batch -pw $VPS_PASS templates/wallet.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/wallet.html

# Force Restart
echo "Restarting service..."
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "supervisorctl restart dice"
echo "Done."
