
$VPS_IP = "72.62.150.44"
$VPS_USER = "root"
$VPS_PASS = "@@ZAzo8965Quophi"
$REPO_URL = "https://github.com/Razisky-Dev/DICE-final.git"

Write-Host "Connecting to Hostinger VPS at $VPS_IP..." -ForegroundColor Green

# Using plink for SSH connection
# Note: We use -batch to avoid interactive prompts
echo y | plink.exe -batch -ssh $VPS_USER@$VPS_IP -pw $VPS_PASS @"
set -e

# Update system
echo "Updating system..."
apt-get update -y
# apt-get upgrade -y # Skipping upgrade to save time

# Ensure git and python
apt-get install -y git python3 python3-pip python3-venv nginx supervisor

# Clone or update repository
if [ -d "/var/www/dice" ]; then
    echo "Pulling latest code..."
    cd /var/www/dice
    git reset --hard
    git pull origin main
else
    echo "Cloning repository..."
    git clone $REPO_URL /var/www/dice
    cd /var/www/dice
fi

# Create virtual environment
echo "Setting up venv..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Setup .env if missing 
if [ ! -f .env ]; then
    cp .env.example .env
fi

# Initialize database
echo "Initing DB..."
python3 init_db.py
python3 migrate_all.py

# --- FIX ADMIN LOGIN ---
echo "Applying Admin Login Fix..."
cat > fix_admin_remote.py << 'EOF'
import os
from app import app, db, User, generate_password_hash
from sqlalchemy import text

def fix_admin():
    with app.app_context():
        # Ensure table exists
        db.create_all()
        
        # Find existing admin
        admin = User.query.filter_by(is_admin=True).first()
        
        if admin:
            print(f"Found Admin User: {admin.email}")
            admin.password = generate_password_hash("admin123")
            db.session.commit()
            print("Password reset to: admin123")
        else:
            print("No Admin User found. Creating one...")
            admin = User(
                first_name="Super",
                last_name="Admin",
                username="admin",
                email="admin@razilhub.com",
                mobile="0000000000",
                password=generate_password_hash("admin123"),
                is_admin=True,
                is_super_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Created Admin User: admin@razilhub.com / admin123")
            
fix_admin()
EOF

python3 fix_admin_remote.py
rm fix_admin_remote.py
# -----------------------

# Setup supervisor
echo "Configuring Supervisor..."
cat > /etc/supervisor/conf.d/dice.conf << 'EOF_SUP'
[program:dice]
command=/var/www/dice/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=/var/www/dice
user=root
autostart=true
autorestart=true
stdout_logfile=/var/log/dice.log
stderr_logfile=/var/log/dice_err.log
EOF_SUP

# Setup nginx
echo "Configuring Nginx..."
cat > /etc/nginx/sites-available/dice << 'EOF_NGINX'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
}
EOF_NGINX

ln -sf /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Restart services
echo "Restarting Services..."
supervisorctl reread
supervisorctl update
supervisorctl restart dice
systemctl restart nginx

echo "Deployment completed!"
"@
