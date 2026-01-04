$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'

# 1. CD to app dir and run python migration
# 1. CD to app dir and run python migration
plink -batch -ssh -pw $PASS $USER@$VPS_IP "cd /var/www/dice; git pull origin main; source venv/bin/activate; python3 update_schema_order_phone.py; python3 update_schema_timestamp.py; python3 update_super_admin_schema.py; python3 update_schema_dealer_price.py; supervisorctl restart dice"
