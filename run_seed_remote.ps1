# Deploy and Run Admin Seeder
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"

# 1. Upload updated seed_admin.py
Write-Host "Uploading seed_admin.py..."
$localScript = Get-Content seed_admin.py -Raw
$remoteCmd = "cat > /var/www/dice/seed_admin.py"
$localScript | & $PLINK -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS $remoteCmd

# 2. Run it
Write-Host "Running seed_admin.py..."
& $PLINK -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "/var/www/dice/venv/bin/python /var/www/dice/seed_admin.py"
