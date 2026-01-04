
import os
from app import app, db, User, generate_password_hash, check_password_hash

def diagnose_user(email, password_attempt):
    with app.app_context():
        print(f"Checking user: {email}")
        user = User.query.filter_by(email=email).first()
        if not user:
            # Try case-insensitive
            from sqlalchemy import func
            user = User.query.filter(func.lower(User.email) == email.lower()).first()
            if user:
                print(f"User found via case-insensitive search: {user.email}")
            else:
                print("User NOT found.")
                # List all users
                all_users = User.query.all()
                print(f"Total users in DB: {len(all_users)}")
                for u in all_users:
                    print(f" - ID: {u.id}, Email: {u.email}, Admin: {u.is_admin}")
                return

        print(f"User found: ID={user.id}, Email={user.email}, IsAdmin={user.is_admin}")
        
        # Check password
        is_valid = check_password_hash(user.password, password_attempt)
        print(f"Password '{password_attempt}' valid? {is_valid}")
        
        if not is_valid:
            print("Password hash in DB:", user.password)
            # Generate what it should be
            new_hash = generate_password_hash(password_attempt)
            print(f"Expected hash format for '{password_attempt}': {new_hash}")

if __name__ == "__main__":
    # Ask for input or hardcode common test
    print("--- Login Diagnosis Tool ---")
    # We can diagnose the known admin email or super admin
    # Based on previous history, admin might be 'admin@dice.com' or similar?
    # Or 'admin@razilhub.com' from app.py line 732
    
    target_email = "admin@razilhub.com" 
    target_password = "admin" # Commonly used or we can ask the user.
    # But usually, I'll just list users first.
    
    with app.app_context():
        users = User.query.all()
        print(f"Found {len(users)} users.")
        for u in users:
             print(f"User: {u.email} | Admin: {u.is_admin}")
