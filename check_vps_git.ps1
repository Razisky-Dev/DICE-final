$pass = '@@ZAzo8965Quophi'
& plink.exe -ssh root@72.62.150.44 -pw $pass -batch "cd /var/www/dice && git log -1"
