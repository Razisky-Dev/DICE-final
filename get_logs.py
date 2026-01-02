
import paramiko

HOSTNAME = "72.62.150.44"
USERNAME = "root"
PASSWORD = "@@ZAzo8965Quophi"

def get_logs():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOSTNAME, username=USERNAME, password=PASSWORD)
        print("--- Gunicorn Logs ---")
        stdin, stdout, stderr = client.exec_command("journalctl -u dice -n 50 --no-pager")
        print(stdout.read().decode())
        print(stderr.read().decode())
    except Exception as e:
        print(e)
    finally:
        client.close()

if __name__ == "__main__":
    get_logs()
