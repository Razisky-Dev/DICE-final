$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'

Write-Host "Resetting Super Admin..." -ForegroundColor Cyan
plink -batch -ssh -pw $PASS $USER@$VPS_IP "cd /var/www/dice; git pull origin main; source venv/bin/activate; python3 reset_super_admin.py"














