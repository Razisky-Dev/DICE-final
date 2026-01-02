$VPS_IP = "72.62.150.44"
$USER = "root"
$PASS = '@@ZAzo8965Quophi'

plink -batch -ssh -pw $PASS $USER@$VPS_IP "journalctl -u dice.service -n 50 --no-pager"
