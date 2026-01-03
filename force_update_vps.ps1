$pass = '@@ZAzo8965Quophi'
$cmds = "cd /var/www/dice && git fetch origin && git reset --hard origin/main && supervisorctl restart dice && systemctl restart nginx"
& plink.exe -ssh root@72.62.150.44 -pw $pass -batch $cmds
