# Quick Start - Deploy DICE to Hostinger VPS

## 🚀 Fastest Deployment Method

### Option 1: One-Command Deployment (Recommended)

Open PowerShell in your project directory and run:

```powershell
.\deploy_simple.ps1
```

This will guide you through the deployment process.

### Option 2: Direct SSH Deployment

Connect to your VPS and run:

```bash
ssh root@72.62.150.44
```

Then execute:

```bash
cd /var/www
git clone https://github.com/Razisky-Dev/DICE-final.git dice
cd dice
chmod +x deploy_complete.sh
./deploy_complete.sh
```

### Option 3: One-Liner from Windows

```powershell
plink.exe -ssh root@72.62.150.44 -pw @@ZAzo8965Quophi "cd /var/www && git clone https://github.com/Razisky-Dev/DICE-final.git dice 2>/dev/null || (cd dice && git pull) && cd dice && chmod +x deploy_complete.sh && ./deploy_complete.sh"
```

## ✅ What the Deployment Does

1. ✅ Updates system packages
2. ✅ Installs Python, Nginx, Git, and required tools
3. ✅ Clones your repository from GitHub
4. ✅ Creates Python virtual environment
5. ✅ Installs all dependencies (Flask, Gunicorn, etc.)
6. ✅ Creates `.env` file with secure SECRET_KEY
7. ✅ Initializes database
8. ✅ Configures Gunicorn service (systemd)
9. ✅ Configures Nginx reverse proxy
10. ✅ Starts all services

## 🔍 Verify Deployment

After deployment, your app should be live at:
```
http://72.62.150.44
```

Check service status:
```bash
systemctl status dice
systemctl status nginx
```

View logs:
```bash
journalctl -u dice -f
```

## 🔄 Updating Your App

After making changes to your code:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Update on server:**
   ```bash
   ssh root@72.62.150.44
   cd /var/www/dice
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt  # If dependencies changed
   systemctl restart dice
   ```

## 📁 Important Files & Locations

- **Application:** `/var/www/dice`
- **Environment Config:** `/var/www/dice/.env`
- **Database:** `/var/www/dice/instance/database.db`
- **Service Config:** `/etc/systemd/system/dice.service`
- **Nginx Config:** `/etc/nginx/sites-available/dice`
- **Logs:** `journalctl -u dice -f`

## 🛠️ Common Commands

```bash
# Restart application
systemctl restart dice

# Restart Nginx
systemctl restart nginx

# View application logs
journalctl -u dice -f

# Check service status
systemctl status dice

# Stop application
systemctl stop dice

# Start application
systemctl start dice
```

## 🔒 Security Notes

1. ⚠️ **Change the root password** after first deployment
2. ⚠️ **Update `.env` file** with your email credentials if needed
3. ⚠️ **Setup firewall:**
   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```
4. ⚠️ **Setup SSL/HTTPS** using Let's Encrypt for production

## 📞 Troubleshooting

### App not loading?
```bash
# Check if service is running
systemctl status dice

# Check logs
journalctl -u dice -n 50

# Check if port is in use
netstat -tulpn | grep 8000
```

### Nginx errors?
```bash
# Test configuration
nginx -t

# Check error logs
tail -f /var/log/nginx/error.log
```

### Permission issues?
```bash
chown -R root:root /var/www/dice
chmod -R 755 /var/www/dice
```

## 📚 Full Documentation

See `DEPLOYMENT.md` for detailed deployment instructions.

---

**Ready to deploy?** Run `.\deploy_simple.ps1` or follow Option 2 above! 🚀

