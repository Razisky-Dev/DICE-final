
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Copy File
echo y | pscp.exe -batch -pw $VPS_PASS templates/login.html $VPS_USER@$VPS_IP`:/var/www/dice/templates/login.html

# Restart not strictly needed for template change in Flask if DEBUG is on, 
# but Gunicorn usually caches templates or pyc. Restart is safer.
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "supervisorctl restart dice"
