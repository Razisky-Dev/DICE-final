from app import app, db, User

def update_username():
    with app.app_context():
        # Find the admin user by old username
        admin = User.query.filter_by(username="DICESS").first()
        
        if not admin:
            # Fallback search by email if username doesn't match
            admin = User.query.filter_by(email="bytemedeals@gmail.com").first()

        if not admin:
            print("Error: Admin user not found.")
            return

        print(f"Found Admin User: {admin.username}")

        # Update Username
        admin.username = "DICCESS"

        try:
            db.session.commit()
            print("SUCCESS: Username updated to DICCESS")
        except Exception as e:
            db.session.rollback()
            print(f"FAILED to update: {str(e)}")

if __name__ == "__main__":
    update_username()
