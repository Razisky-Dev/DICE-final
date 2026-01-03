from app import app, db, User
from werkzeug.security import check_password_hash

def debug_login():
    with app.app_context():
        email = "bytemedeals@gmail.com"
        password = "Quophi@2"
        
        print(f"--- DEBUG LOGIN: {email} ---")
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print("RESULT: User NOT FOUND.")
            # List all users to see if there's a typo
            all_users = User.query.all()
            print("Existing Users:")
            for u in all_users:
                print(f" - {u.email} (Username: {u.username})")
            return

        print(f"RESULT: User Found (ID: {user.id})")
        print(f" - Username: {user.username}")
        print(f" - Is Admin: {user.is_admin}")
        print(f" - Is Super Admin: {user.is_super_admin}")
        print(f" - Is Suspended: {user.is_suspended}")
        print(f" - Stored Hash: {user.password[:20]}...")
        
        # Check Password
        is_valid = check_password_hash(user.password, password)
        print(f" - Password Check ('{password}'): {'VALID' if is_valid else 'INVALID'}")
        
        if not is_valid:
            print("!!! PASSWORD MISMATCH !!!")
        
        if user.is_suspended:
            print("!!! USER IS SUSPENDED !!!")

if __name__ == "__main__":
    debug_login()
