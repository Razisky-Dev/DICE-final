$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'

# 1. CD to app dir and run python migration
plink -batch -ssh -pw $PASS $USER@$VPS_IP "cd /var/www/dice; source venv/bin/activate; python3 update_schema_order_phone.py"
