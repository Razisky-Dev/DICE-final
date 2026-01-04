
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# 1. Copy Fix Script
echo y | pscp.exe -batch -pw $VPS_PASS fix_admin_login_final.py $VPS_USER@$VPS_IP`:/var/www/dice/fix_admin_login_final.py

# 2. Run Deployment Script via pipe
# We read the file and pipe it to plink bash
type deploy_internal.sh | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS bash
