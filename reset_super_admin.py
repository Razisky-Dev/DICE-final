from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_super_admin():
    with app.app_context():
        target_email = "bytemedeals@gmail.com"
        target_password = "Quophi@2"
        target_username = "SuperAdminByteMe" # Updated to reflect new email context if needed, or keep generic
        
        print(f"Configuring Super Admin: {target_email}")
        
        # Check if user exists by email
        user = User.query.filter_by(email=target_email).first()
        
        if user:
            print(f"User found: {user.username}. Updating credentials...")
            user.password = generate_password_hash(target_password)
            user.is_admin = True
            user.is_super_admin = True
            if not user.preferred_network:
                user.preferred_network = "MTN"
            print("Credentials updated.")
        else:
            print("User not found. Creating new Super Admin...")
            new_user = User(
                first_name="Super",
                last_name="Admin",
                username=target_username,
                email=target_email,
                mobile="0550000000",
                password=generate_password_hash(target_password),
                is_admin=True,
                is_super_admin=True,
                preferred_network="MTN"
            )
            db.session.add(new_user)
            print("New Super Admin created.")
            
        db.session.commit()
        print("Success.")

if __name__ == "__main__":
    reset_super_admin()
