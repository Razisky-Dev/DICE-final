
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# 1. Copy Script (already there, but safe to redo)
echo y | pscp.exe -batch -pw $VPS_PASS debug_db_path.py $VPS_USER@$VPS_IP`:/var/www/dice/debug_db_path.py

# 2. Run Script using VENV python
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cd /var/www/dice && ./venv/bin/python debug_db_path.py && rm debug_db_path.py"
