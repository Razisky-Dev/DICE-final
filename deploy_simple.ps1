# Simple Deployment Script - Uses SCP + SSH
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DICE Application Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check for required tools
$plinkPath = Get-Command plink.exe -ErrorAction SilentlyContinue
$pscpPath = Get-Command pscp.exe -ErrorAction SilentlyContinue

if (-not $plinkPath) {
    Write-Host "Error: plink.exe not found. Please install PuTTY." -ForegroundColor Red
    exit 1
}

if (-not $pscpPath -and -not (Test-Path "pscp.exe")) {
    Write-Host "Warning: pscp.exe not found. Will use SSH method instead." -ForegroundColor Yellow
    Write-Host ""
}

# Check if deployment script exists
if (-not (Test-Path "deploy_complete.sh")) {
    Write-Host "Error: deploy_complete.sh not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Method 1: Manual SSH Deployment (Recommended)" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "1. Connect to your VPS:" -ForegroundColor Yellow
Write-Host "   plink.exe -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS" -ForegroundColor White
Write-Host ""
Write-Host "2. Once connected, run these commands:" -ForegroundColor Yellow
Write-Host "   cd /var/www" -ForegroundColor White
Write-Host "   git clone https://github.com/Razisky-Dev/DICE-final.git dice" -ForegroundColor White
Write-Host "   cd dice" -ForegroundColor White
Write-Host "   chmod +x deploy_complete.sh" -ForegroundColor White
Write-Host "   ./deploy_complete.sh" -ForegroundColor White
Write-Host ""
Write-Host "OR use this one-liner:" -ForegroundColor Cyan
Write-Host "plink.exe -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS `"cd /var/www && git clone https://github.com/Razisky-Dev/DICE-final.git dice 2>/dev/null || (cd dice && git pull) && cd dice && chmod +x deploy_complete.sh && ./deploy_complete.sh`"" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Would you like to run the automated deployment now? (Y/N)"

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Deploying..." -ForegroundColor Yellow
    Write-Host ""
    
    $deployCommand = @"
cd /var/www
if [ -d "dice/.git" ]; then
    cd dice
    git pull origin main
else
    git clone https://github.com/Razisky-Dev/DICE-final.git dice
    cd dice
fi
chmod +x deploy_complete.sh
bash deploy_complete.sh
"@
    
    try {
        & plink.exe -ssh "$VPS_USER@$VPS_IP" -pw $VPS_PASS -batch $deployCommand
        
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host "Deployment completed!" -ForegroundColor Green
        Write-Host "==========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your application should be available at:" -ForegroundColor Cyan
        Write-Host "http://$VPS_IP" -ForegroundColor White
        Write-Host ""
        
    } catch {
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please try the manual method above." -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Deployment cancelled. Use the manual method above when ready." -ForegroundColor Yellow
}
