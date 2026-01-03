# Deploy .env to VPS
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

Write-Host "Reading local .env..."
$envContent = Get-Content .env -Raw

Write-Host "Uploading to $VPS_IP..."
# Use a temporary file approach or Python if PowerShell piping is finicky.
# Safe bet: Python script? No, PowerShell is fine if we use input object.

$plink = "plink.exe"
$remoteCmd = "cat > /var/www/dice/.env"
$catArgs = @("-batch", "-ssh", "$VPS_USER@$VPS_IP", "-pw", "$VPS_PASS", $remoteCmd)

# Send content to plink's stdin
$envContent | & $plink $catArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload successful." -ForegroundColor Green
    
    Write-Host "Restarting dice service..."
    $restartCmd = "supervisorctl restart dice"
    & $plink -batch -ssh "$VPS_USER@$VPS_IP" -pw "$VPS_PASS" $restartCmd
    
    Write-Host "Service restarted." -ForegroundColor Green
} else {
    Write-Host "Upload failed." -ForegroundColor Red
}
