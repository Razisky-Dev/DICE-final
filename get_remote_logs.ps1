# Read credentials from local .env file
$envParams = @{}
Get-Content .env | ForEach-Object {
    if ($_ -match '^(.*?)=(.*)$') {
        $envParams[$matches[1]] = $matches[2]
    }
}

$VPS_IP = $envParams["VPS_IP"]
$USER = $envParams["VPS_USER"]
$PASS = $envParams["VPS_PASS"]

if (-not $VPS_IP -or -not $PASS) {
    Write-Error "Could not find VPS_IP or VPS_PASS in .env file."
    exit 1
}

# Fetch both supervisor stderr logs and journalctl
Write-Host "Fetching Supervisor Error Logs..." -ForegroundColor Cyan
plink -batch -ssh -pw $PASS $USER@$VPS_IP "tail -n 50 /var/log/dice_err.log"

Write-Host "`nFetching Journalctl Logs..." -ForegroundColor Cyan
plink -batch -ssh -pw $PASS $USER@$VPS_IP "journalctl -u dice.service -n 20 --no-pager"

plink -batch -ssh -pw $PASS $USER@$VPS_IP "journalctl -u dice.service -n 50 --no-pager"
