$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'
$APP_DIR = "/var/www/dice"

# Helper for Plink
function Run-Plink {
    param($cmd)
    Write-Host "Running on VPS: $cmd" -ForegroundColor Gray
    plink -batch -ssh -pw $PASS $USER@$VPS_IP $cmd
}

Write-Host "Finishing Deployment..." -ForegroundColor Cyan

# 1. Upload setup script
Write-Host "Uploading setup script..." -ForegroundColor Yellow
pscp -batch -pw $PASS ./vps_setup.sh ${USER}@${VPS_IP}:${APP_DIR}/

# 2. Fix line endings and run
Write-Host "Executing setup script..." -ForegroundColor Yellow
Run-Plink "cd $APP_DIR; sed -i 's/\r$//' vps_setup.sh; bash vps_setup.sh"

Write-Host "Deployment Finalized! Visit http://$VPS_IP" -ForegroundColor Green
