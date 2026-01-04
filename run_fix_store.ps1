
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Copy Script
echo y | pscp.exe -batch -pw $VPS_PASS fix_schema_store.py $VPS_USER@$VPS_IP`:/var/www/dice/fix_schema_store.py

# Run Script & Restart
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cd /var/www/dice && ./venv/bin/python fix_schema_store.py && rm fix_schema_store.py && supervisorctl restart dice"
