
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Copy Files (Only the fixed ones)
echo y | pscp.exe -batch -pw $VPS_PASS app.py $VPS_USER@$VPS_IP`:/var/www/dice/app.py
echo y | pscp.exe -batch -pw $VPS_PASS templates/admin/stores.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/admin/stores.html

# Force Restart
echo "Restarting service..."
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "supervisorctl restart dice"
echo "Done."
