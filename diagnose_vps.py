
import paramiko
import time

VPS_IP = "72.62.150.44"
USER = "root"
PASSWORD = "@@ZAzo8965Quophi"

def diagnose():
    print(f"Connecting to {VPS_IP} for migration...")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_IP, username=USER, password=PASSWORD)
        print("Connected!")

        commands = [
            "source /var/www/dice/venv/bin/activate && python3 /var/www/dice/update_schema_timestamp.py",
            "systemctl restart dice"
        ]

        for cmd in commands:
            print(f"\n--- Executing: {cmd} ---")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # Wait for exit status to ensure sequential execution
            exit_status = stdout.channel.recv_exit_status()
            
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            
            if out: print(out)
            if err: print(f"STDERR: {err}")
            
        ssh.close()
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    diagnose()
