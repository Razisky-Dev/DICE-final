
import os
from app import app, db, User, generate_password_hash

def fix_admin():
    with app.app_context():
        # Find existing admin
        admin = User.query.filter_by(is_admin=True).first()
        
        if admin:
            print(f"Found Admin User: {admin.email}")
            admin.password = generate_password_hash("admin123")
            db.session.commit()
            print("Password reset to: admin123")
        else:
            print("No Admin User found. Creating one...")
            admin = User(
                first_name="Super",
                last_name="Admin",
                username="admin",
                email="admin@dice.com",
                mobile="0000000000",
                password=generate_password_hash("admin123"),
                is_admin=True,
                is_super_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Created Admin User: admin@dice.com / admin123")

if __name__ == "__main__":
    fix_admin()
