
import paramiko
import time

VPS_IP = "72.62.150.44"
USER = "root"
PASSWORD = "@@ZAzo8965Quophi"
APP_DIR = "/var/www/dice"

commands = [
    # 1. Allow Git to operate
    "git config --global --add safe.directory /var/www/dice",

    # 2. Backup Database (Safety First!)
    f"cp {APP_DIR}/instance/database.db {APP_DIR}/instance/database.db.backup_v2",

    # 3. Force Git Pull (Discard server changes to tracked files)
    f"cd {APP_DIR} && git fetch origin && git reset --hard origin/main",
    
    # 4. Restore Database (If it got deleted/overwritten)
    f"mv {APP_DIR}/instance/database.db.backup_v2 {APP_DIR}/instance/database.db",
    
    # 5. Fix permissions again just in case
    f"chown -R www-data:www-data {APP_DIR}",

    # 6. Restart Services
    "systemctl restart dice",
    "systemctl restart nginx"
]

def run_deploy():
    print(f"Connecting to {VPS_IP}...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=USER, password=PASSWORD)
        print("Connected!")

        for cmd in commands:
            print(f"Executing: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            
            if out: print(out)
            if err: print(f"Error: {err}")
            
            if exit_status != 0:
                print(f"Command failed with status {exit_status}")
                
        print("\nDeployment Fixes Completed Successfully.")

        # Run Database Migrations
        print("Running database migrations...")
        # The original command was:
        # stdin, stdout, stderr = ssh.exec_command(f"cd {APP_DIR} && source venv/bin/activate && python3 update_schema_timestamp.py && python3 update_schema_order_phone.py")
        
        # Update schema for timestamp
        stdin, stdout, stderr = ssh.exec_command(f'cd {APP_DIR} && {APP_DIR}/venv/bin/python3 update_schema_timestamp.py')
        print(f"Updating User table with 'last_read_notice_timestamp' column...")
        err = stderr.read().decode()
        if err:
             print(f"Column update error (might already exist): {err}")
        
        # Update schema for order phone (if needed, based on original code)
        stdin, stdout, stderr = ssh.exec_command(f'cd {APP_DIR} && {APP_DIR}/venv/bin/python3 update_schema_order_phone.py')
        print(stdout.read().decode())
        print(stderr.read().decode())

        # Run the Big Time fix script
        print("Running DB Fix for 'Big Time' names...")
        stdin, stdout, stderr = ssh.exec_command(f'cd {APP_DIR} && {APP_DIR}/venv/bin/python3 fix_db_plans.py')
        print(stdout.read().decode())
        print(stderr.read().decode())

        try:
            # Verify Deployment
            print("\n--- Verifying Remote Files ---")
            
            # Check admin/base.html for v=5
            stdin, stdout, stderr = ssh.exec_command('grep "v=5" /var/www/dice/templates/admin/base.html')
            res = stdout.read().decode().strip()
            if res:
                print(f"[SUCCESS] Found v=5 in admin/base.html: {res}")
            else:
                print("[FAILURE] v=5 NOT found in admin/base.html")

            # Check admin/transactions.html for 'Actions' (Should be absent)
            stdin, stdout, stderr = ssh.exec_command('grep "Actions" /var/www/dice/templates/admin/transactions.html')
            res = stdout.read().decode().strip()
            if not res:
                print("[SUCCESS] 'Actions' column successfully REMOVED from transactions.html")
            else:
                print(f"[FAILURE] Found 'Actions' in transactions.html: {res}")

        except Exception as e:
            print(f"Error during verification: {e}")

        print("\nDeployment Cycle Complete.")
        ssh.close()
        
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    run_deploy()
