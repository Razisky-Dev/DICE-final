from app import app, db, User, Store

def set_credit():
    with app.app_context():
        # Find Admin User
        user = User.query.filter_by(username="DICCESS").first()
        if not user:
            print("User DICCESS not found")
            return

        # Find Store
        store = Store.query.filter_by(user_id=user.id).first()
        
        if not store:
            print("No store found for DICCESS.")
            return
        
        # Set Credit to 50.00
        store.credit_balance = 50.00
        db.session.commit()
        
        print(f"Set Store Credit to GHc 50.00 for '{store.name}'.")

if __name__ == "__main__":
    set_credit()
