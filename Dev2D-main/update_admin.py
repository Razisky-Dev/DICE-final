from app import app, db, User
from sqlalchemy import text
from werkzeug.security import generate_password_hash

print("Updating User table with 'is_admin' column...")

with app.app_context():
    # 1. Add Column
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
        print("Column 'is_admin' added successfully.")
    except Exception as e:
        print(f"Column update error (might already exist): {e}")

    # 2. Create/Update Admin User
    admin_email = "admin@dice.com"
    admin = User.query.filter_by(email=admin_email).first()
    
    if not admin:
        print(f"Creating default admin: {admin_email}")
        new_admin = User(
            first_name="Super",
            last_name="Admin",
            username="admin",
            email=admin_email,
            mobile="0000000000",
            password=generate_password_hash("admin123"),
            is_admin=True,
            balance=0.0
        )
        db.session.add(new_admin)
    else:
        print(f"Admin user {admin_email} exists. Ensuring admin privileges...")
        admin.is_admin = True
        
    db.session.commit()
    print("Admin user setup complete.")
