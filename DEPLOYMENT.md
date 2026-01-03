# DICE Application Deployment Guide

## Quick Deployment

### Option 1: Automated Deployment (PowerShell)

From Windows, run:
```powershell
.\deploy.ps1
```

This will automatically:
- Connect to your VPS via SSH
- Clone/update the repository
- Set up Python virtual environment
- Install dependencies
- Configure Gunicorn service
- Configure Nginx
- Start all services

### Option 2: Manual Deployment (SSH)

1. **Connect to your VPS:**
   ```bash
   ssh root@72.62.150.44
   ```

2. **Run the deployment script:**
   ```bash
   cd /var/www
   git clone https://github.com/Razisky-Dev/DICE-final.git dice
   cd dice
   chmod +x deploy_complete.sh
   ./deploy_complete.sh
   ```

## Manual Step-by-Step Deployment

If you prefer to deploy manually:

### 1. Update System
```bash
apt update && apt upgrade -y
```

### 2. Install Dependencies
```bash
apt install -y python3 python3-pip python3-venv git nginx systemd
```

### 3. Clone Repository
```bash
cd /var/www
git clone https://github.com/Razisky-Dev/DICE-final.git dice
cd dice
```

### 4. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 5. Configure Environment Variables
```bash
# Create .env file
cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
SQLALCHEMY_DATABASE_URI=sqlite:///instance/database.db
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
SITE_NAME=RazilHub
EOF
```

### 6. Initialize Database
```bash
mkdir -p instance
python3 init_db.py
```

### 7. Setup Gunicorn Service
```bash
cp vps_config/dice.service /etc/systemd/system/dice.service
systemctl daemon-reload
systemctl enable dice
systemctl start dice
```

### 8. Configure Nginx
```bash
cp vps_config/dice_nginx /etc/nginx/sites-available/dice
ln -sf /etc/nginx/sites-available/dice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

## Verification

After deployment, verify everything is working:

1. **Check Gunicorn service:**
   ```bash
   systemctl status dice
   ```

2. **Check Nginx:**
   ```bash
   systemctl status nginx
   ```

3. **View application logs:**
   ```bash
   journalctl -u dice -f
   ```

4. **Test in browser:**
   Open: `http://72.62.150.44`

## Updating the Application

To update the application after making changes:

```bash
cd /var/www/dice
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart dice
```

## Troubleshooting

### Service won't start
```bash
# Check logs
journalctl -u dice -n 50

# Check if port is in use
netstat -tulpn | grep 8000
```

### Nginx errors
```bash
# Test configuration
nginx -t

# Check error logs
tail -f /var/log/nginx/error.log
```

### Permission issues
```bash
# Ensure correct ownership
chown -R root:root /var/www/dice
chmod -R 755 /var/www/dice
```

### Database issues
```bash
cd /var/www/dice
source venv/bin/activate
python3 init_db.py
```

## Security Recommendations

1. **Change default root password** after first login
2. **Setup firewall:**
   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```
3. **Setup SSL/HTTPS** using Let's Encrypt
4. **Regular updates:**
   ```bash
   apt update && apt upgrade -y
   ```

## Important Files

- Application code: `/var/www/dice`
- Environment config: `/var/www/dice/.env`
- Database: `/var/www/dice/instance/database.db`
- Service config: `/etc/systemd/system/dice.service`
- Nginx config: `/etc/nginx/sites-available/dice`
- Service logs: `journalctl -u dice`

## Support

For issues, check:
1. Service logs: `journalctl -u dice -f`
2. Nginx logs: `/var/log/nginx/error.log`
3. Application logs in journalctl

