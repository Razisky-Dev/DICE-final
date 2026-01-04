import requests
import sys

# VPS config
BASE_URL = "http://127.0.0.1:8000" # Running via gunicorn/supervisor usually on port 8000 or similar, or just check 72.62.150.44 if public
# Actually, since we are running ON the VPS, we can hit 127.0.0.1 if we know the port.
# If nginx is proxying fast pass, likely a sock file or local port.
# Let's try http://localhost/ if nginx is serving it map to domain.

# But easier to use Flask test client!
from app import app

def verify_pages():
    print("Initializing Flask Test Client...")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        # 1. Login
        print("Logging in...")
        resp = client.post('/admin/login', data={
            'email': 'admin@razilhub.com', # Assuming this is the admin
            'password': 'admin123'         # Assuming this is the pass
        }, follow_redirects=True)
        
        if b"Dashboard" in resp.data or resp.status_code == 200:
             print("Login successful (or at least returned 200).")
        else:
             print(f"Login might have failed. Status: {resp.status_code}")
             # print(resp.data[:200])

        # 2. Check Pages
        pages = [
            '/admin/stores',
            '/admin/orders',
            '/admin/transactions'
        ]
        
        for p in pages:
            print(f"Checking {p}...")
            try:
                resp = client.get(p, follow_redirects=True)
                if resp.status_code == 200:
                    print(f"  [OK] {p} returned 200")
                elif resp.status_code == 500:
                    print(f"  [FAIL] {p} returned 500 INTERNAL SERVER ERROR")
                else:
                    print(f"  [WARN] {p} status {resp.status_code}")
            except Exception as e:
                print(f"  [EXCEPTION] {e}")

if __name__ == "__main__":
    verify_pages()
