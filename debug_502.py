
import paramiko
import time

HOSTNAME = "72.62.150.44"
USERNAME = "root"
PASSWORD = "@@ZAzo8965Quophi"

def debug_vps():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOSTNAME}...")
        client.connect(HOSTNAME, username=USERNAME, password=PASSWORD)
        print("Connected!")
        
        commands = [
            "systemctl status dice",
            "journalctl -u dice -n 50 --no-pager",
            "tail -n 20 /var/log/nginx/error.log",
            "python3 -m py_compile /var/www/dice/app.py" # Check for syntax errors directly
        ]
        
        for cmd in commands:
            print(f"\n--- Executing: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            
            if out: print(out)
            if err: print(f"ERROR/STDERR: {err}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_vps()
