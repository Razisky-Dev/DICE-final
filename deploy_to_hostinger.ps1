# Deploy to Hostinger VPS
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$REPO_URL = "https://github.com/Razisky-Dev/DICE-final.git"

Write-Host "Connecting to Hostinger VPS at $VPS_IP..." -ForegroundColor Green

# Using plink for SSH connection
plink.exe -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS @"
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv git nginx supervisor

# Clone or update repository
if [ -d "/var/www/dice" ]; then
    cd /var/www/dice
    git pull origin main
else
    git clone $REPO_URL /var/www/dice
    cd /var/www/dice
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your actual values

# Initialize database
python init_db.py

# Setup supervisor
cat > /etc/supervisor/conf.d/dice.conf << EOF
[program:dice]
command=/var/www/dice/venv/bin/python app.py
directory=/var/www/dice
user=www-data
autostart=true
autorestart=true
stdout_logfile=/var/log/dice.log
stderr_logfile=/var/log/dice_err.log
EOF

# Setup nginx
cat > /etc/nginx/sites-available/dice << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -s /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Restart services
supervisorctl reread
supervisorctl update
supervisorctl start dice
systemctl restart nginx

echo "Deployment completed!"
echo "Your DICE app should be running at http://$VPS_IP"
"@

Write-Host "Deployment completed!" -ForegroundColor Green
