
from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Check if admin exists by username OR email
        admin = User.query.filter((User.email == "admin@razilhub.com") | (User.username == "admin")).first()

        if admin:
            # Update existing user to be admin with known password
            admin.username = "admin"
            admin.email = "admin@razilhub.com"
            admin.password = generate_password_hash("admin123")
            admin.is_admin = True
            print(f"Admin user 'admin' updated. Password reset to 'admin123'.")
        else:
            # Create new admin
            new_admin = User(
                username="admin",
                email="admin@razilhub.com",
                password=generate_password_hash("admin123"),
                mobile="0000000000",
                is_admin=True
            )
            db.session.add(new_admin)
            print(f"Admin user 'admin' created. Password set to 'admin123'.")

        db.session.commit()

if __name__ == "__main__":
    create_admin_user()
