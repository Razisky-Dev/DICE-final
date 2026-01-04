
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Copy Dashboard Template
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/dashboard.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/dashboard.html

# Force Restart
echo "Restarting service..."
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "supervisorctl restart dice"
echo "Done."
