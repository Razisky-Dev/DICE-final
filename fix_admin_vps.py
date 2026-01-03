from app import app, db, User
from werkzeug.security import generate_password_hash
import sys

def fix_admin():
    with app.app_context():
        print("--- DEBUGGING ADMIN LOGIN ---")
        
        # 1. List all users to see what's in DB
        users = User.query.all()
        print(f"Total Users in DB: {len(users)}")
        for u in users:
            print(f"ID: {u.id} | Email: {u.email} | Admin: {u.is_admin} | Suspended: {u.is_suspended}")

        # 2. Reset Admin
        email = "admin@razilhub.com"
        username = "admin"
        admin = User.query.filter_by(email=email).first()

        if not admin:
            print(f"Admin user {email} NOT FOUND. Creating new...")
            admin = User(
                username=username,
                email=email,
                first_name="Admin",
                last_name="User",
                mobile="0000000000",
                is_admin=True,
                is_super_admin=True
            )
            db.session.add(admin)
        else:
            print(f"Admin user found. Resetting attributes...")
            admin.is_admin = True
            admin.is_super_admin = True # Ensure super admin
            admin.is_suspended = False

        # Force Password Reset
        new_pass = "admin123"
        admin.password = generate_password_hash(new_pass)
        print(f"Password reset to: {new_pass}")
        
        try:
            db.session.commit()
            print("Successfully committed changes.")
        except Exception as e:
            print(f"Error committing changes: {e}")
            db.session.rollback()

if __name__ == "__main__":
    fix_admin()
