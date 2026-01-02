$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'
$APP_DIR = "/var/www/dice"

Write-Host "Uploading fixed migration script..." -ForegroundColor Yellow
pscp -batch -pw $PASS ./update_schema_order_phone.py ${USER}@${VPS_IP}:${APP_DIR}/

Write-Host "Running migration..." -ForegroundColor Yellow
plink -batch -ssh -pw $PASS $USER@$VPS_IP "cd $APP_DIR; source venv/bin/activate; python3 update_schema_order_phone.py"
