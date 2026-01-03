
from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Check if admin exists by username OR email
        # We look for the specific new super admin or the old one to update
        target_email = "bytemedeals@gmail.com"
        target_username = "SuperAdmin"
        target_pass = "Quophi@2"
        
        admin = User.query.filter((User.email == target_email) | (User.username == target_username)).first()

        if admin:
            # Update existing user to be admin with known password
            admin.username = target_username
            admin.email = target_email
            admin.password = generate_password_hash(target_pass)
            admin.is_admin = True
            admin.is_super_admin = True # Ensure this is set
            admin.preferred_network = "MTN" # Ensure this is set
            print(f"Admin user '{target_username}' updated. Password reset.")
        else:
            # Create new admin
            new_admin = User(
                username=target_username,
                email=target_email,
                password=generate_password_hash(target_pass),
                mobile="0000000000",
                is_admin=True,
                is_super_admin=True, # Ensure this is set
                preferred_network="MTN" # Default value to avoid null constraints or logic errors
            )
            db.session.add(new_admin)
            print(f"Admin user '{target_username}' created. Password set.")

        db.session.commit()

if __name__ == "__main__":
    create_admin_user()
