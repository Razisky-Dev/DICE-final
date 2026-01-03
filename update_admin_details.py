from app import app, db, User
from werkzeug.security import generate_password_hash

def update_admin():
    with app.app_context():
        # Find the admin user (checking multiple identifiers to be safe)
        admin = User.query.filter(
            (User.email == 'admin@razilhub.com') | 
            (User.username == 'admin') |
            (User.is_super_admin == True)
        ).first()

        if not admin:
            print("Error: Super Admin user not found.")
            return

        print(f"Found Admin User: {admin.username} ({admin.email})")

        # Update Details
        admin.username = "DICESS"
        admin.mobile = "0533989919"
        admin.preferred_network = "MTN"
        admin.password = generate_password_hash("Quophi@2")
        
        # Ensure is_admin/super_admin is set just in case
        admin.is_admin = True
        admin.is_super_admin = True

        try:
            db.session.commit()
            print("SUCCESS: Super Admin details updated.")
            print("Username: DICESS")
            print("Mobile: 0533989919")
            print("Network: MTN")
            print("Password: [Updated]")
        except Exception as e:
            db.session.rollback()
            print(f"FAILED to update: {str(e)}")

if __name__ == "__main__":
    update_admin()
