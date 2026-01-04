$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

$remoteScript = @"
    echo "--- DIAGNOSTICS START ---"
    pwd
    ls -la /var/www
    ls -la /var/www/dice
    echo "--- DIAGNOSTICS END ---"
"@

echo $remoteScript | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cat > /tmp/diag.sh && tr -d '\r' < /tmp/diag.sh > /tmp/diag_clean.sh && bash /tmp/diag_clean.sh"
