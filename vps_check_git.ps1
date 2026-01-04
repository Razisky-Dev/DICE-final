$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"

$remoteScript = @"
    echo "--- GIT CHECK START ---"
    cd /var/www/dice
    git pull origin main
    ls -l update_schema_manufacturing.py
    echo "--- GIT CHECK END ---"
"@

echo $remoteScript | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS "cat > /tmp/git_check.sh && tr -d '\r' < /tmp/git_check.sh > /tmp/git_check_clean.sh && bash /tmp/git_check_clean.sh"
