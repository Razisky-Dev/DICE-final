$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'

Write-Host "Forcing VPS Code Update..." -ForegroundColor Cyan
# Force reset to discard any local changes preventing pull
plink -batch -ssh -pw $PASS $USER@$VPS_IP "cd /var/www/dice; git fetch --all; git reset --hard origin/main; chown -R www-data:www-data /var/www/dice; chmod -R 775 /var/www/dice"

Write-Host "Verifying VPS Code Again..." -ForegroundColor Cyan
plink -batch -ssh -pw $PASS $USER@$VPS_IP "grep 'func.lower' /var/www/dice/app.py"

Write-Host "Restarting Services..." -ForegroundColor Cyan
plink -batch -ssh -pw $PASS $USER@$VPS_IP "supervisorctl restart dice; systemctl restart nginx"







