from app import app, db, User

def update_email():
    with app.app_context():
        # Find the admin user by the NEW username we just set
        admin = User.query.filter_by(username="DICESS").first()

        if not admin:
            print("Error: User 'DICESS' not found.")
            return

        print(f"Found Admin User: {admin.username} ({admin.email})")

        # Update Email
        admin.email = "bytemedeals@gmail.com"

        try:
            db.session.commit()
            print("SUCCESS: Admin email updated.")
            print("New Email: bytemedeals@gmail.com")
        except Exception as e:
            db.session.rollback()
            print(f"FAILED to update: {str(e)}")

if __name__ == "__main__":
    update_email()
