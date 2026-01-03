# Deploy and Run Super Admin Updates
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$PLINK = "plink.exe"

# 1. Upload update_super_admin_schema.py
Write-Host "Uploading update_super_admin_schema.py..."
$localSchema = Get-Content update_super_admin_schema.py -Raw
$remoteSchemaCmd = "cat > /var/www/dice/update_super_admin_schema.py"
$localSchema | & $PLINK -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS $remoteSchemaCmd

# 2. Upload updated seed_admin.py
Write-Host "Uploading seed_admin.py..."
$localSeed = Get-Content seed_admin.py -Raw
$remoteSeedCmd = "cat > /var/www/dice/seed_admin.py"
$localSeed | & $PLINK -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS $remoteSeedCmd

# 3. Run migration
Write-Host "Running Schema Update..."
& $PLINK -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "/var/www/dice/venv/bin/python /var/www/dice/update_super_admin_schema.py"

# 4. Run admin seeder
Write-Host "Running Admin Seed..."
& $PLINK -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "/var/www/dice/venv/bin/python /var/www/dice/seed_admin.py"

Write-Host "Done!" -ForegroundColor Green
