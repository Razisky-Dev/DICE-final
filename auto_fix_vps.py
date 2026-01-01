
import paramiko
import time

VPS_IP = "72.62.150.44"
USER = "root"
PASSWORD = "@@ZAzo8965Quophi"
APP_DIR = "/var/www/dice"

commands = [
    # Verify content of style.css to see if fixes are present
    "head -n 50 /var/www/dice/static/css/style.css"
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
        ssh.close()
        
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    run_deploy()
