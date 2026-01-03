from app import app, db, User
from werkzeug.security import check_password_hash
import sys

def health_check():
    with app.app_context():
        print("=== DEEP HEALTH CHECK ===")
        
        # 1. LIST ALL USERS
        users = User.query.all()
        print(f"Total Users: {len(users)}")
        for u in users:
            print(f"ID: {u.id} | Email: '{u.email}' | Username: '{u.username}' | Admin: {u.is_admin} | Super: {u.is_super_admin} | Active: {not u.is_suspended}")
            
        # 2. TARGET USER CHECK
        target_email = "bytemedeals@gmail.com"
        target_pass = "Quophi@2"
        
        print(f"\nChecking Target: {target_email}...")
        user = User.query.filter(User.email == target_email).first() # Case sensitive check first
        
        if not user:
            print(" - Exact match NOT FOUND.")
            # Partial match?
            user = User.query.filter(User.email.ilike(target_email)).first()
            if user:
                print(f" - Case-insensitive match FOUND: '{user.email}'")
            else:
                print(" - NO MATCH FOUND AT ALL.")
                return
        else:
            print(" - Exact match FOUND.")
            
        # 3. VERIFY PASSWORD
        print(f" - Stored Hash: {user.password[:30]}...")
        if check_password_hash(user.password, target_pass):
             print(f" - Password Check: VALID")
        else:
             print(f" - Password Check: INVALID (Hash mismatch)")

        # 4. DB INTEGRITY
        try:
             # Check if there are duplicate emails?
             cnt = User.query.filter(User.email == user.email).count()
             print(f" - Duplicate Count: {cnt} (Should be 1)")
        except Exception as e:
             print(f" - DB Error: {e}")

if __name__ == "__main__":
    health_check()
