$ErrorActionPreference = "Stop"

$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

# Files to update
$FILES = @(
    "templates/login.html",
    "fix_admin_vps.py",
    "static/css/style.css"
)

Write-Host "1. Uploading modified files..." -ForegroundColor Cyan
foreach ($file in $FILES) {
    $remote_path = "/var/www/dice/$file"
    # Ensure directory exists (mostly for deep paths if needed, though templates/login.html exists)
    Write-Host "Uploading $file to $remote_path"
    pscp -pw $VPS_PASS -batch $file ${VPS_USER}@${VPS_IP}:${remote_path}
}

Write-Host "2. Running Admin Fix Script..." -ForegroundColor Cyan
plink -ssh -pw $VPS_PASS -batch ${VPS_USER}@${VPS_IP} "cd /var/www/dice && source venv/bin/activate && python fix_admin_vps.py"

Write-Host "3. Restarting Application..." -ForegroundColor Cyan
plink -ssh -pw $VPS_PASS -batch ${VPS_USER}@${VPS_IP} "supervisorctl restart dice"

Write-Host "Update Complete!" -ForegroundColor Green
