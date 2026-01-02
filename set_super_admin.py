from app import app, db, User

def set_super_admin():
    with app.app_context():
        print("Set Super Admin User")
        print("-" * 20)
        email = input("Enter email of the user to make Super Admin: ").strip()
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print("User not found!")
            return
            
        char = input(f"Are you sure you want to make {user.username} ({user.email}) a SUPER ADMIN? (y/n): ")
        if char.lower() == 'y':
            user.is_admin = True # Ensure they are also admin
            user.is_super_admin = True
            db.session.commit()
            print(f"Success! {user.username} is now a Super Admin.")
        else:
            print("Operation cancelled.")

if __name__ == "__main__":
    set_super_admin()
