$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'

Write-Host "Reading local script..."
$ScriptContent = Get-Content -Path "reset_super_admin.py" -Raw
# Ensure Unix Line Endings
$ScriptContent = $ScriptContent -replace "`r`n", "`n" 

# Write to temp file locally to be safe or use plink with file redirection if supported?
# Plink -m is for local command file. Let's try redirecting.
# Actually, constructing the here-document carefully.

$RemoteCmd = "cat > /var/www/dice/reset_super_admin.py << 'EOF'`n$ScriptContent`nEOF"

Write-Host "Uploading script..."
$Bytes = [System.Text.Encoding]::UTF8.GetBytes($RemoteCmd)
$Encoded = [System.Convert]::ToBase64String($Bytes)

# Use base64 decode on remote to avoid char escaping hell
$DecodeCmd = "echo $Encoded | base64 -d | bash"
plink -batch -ssh -pw $PASS $USER@$VPS_IP $DecodeCmd

Write-Host "Executing script..."
plink -batch -ssh -pw $PASS $USER@$VPS_IP "cd /var/www/dice; source venv/bin/activate; python3 reset_super_admin.py"
