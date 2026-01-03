from app import app, db, User, Store

def add_credit():
    with app.app_context():
        # Find Admin User
        user = User.query.filter_by(username="DICCESS").first()
        if not user:
            print("User DICCESS not found")
            return

        # Find Store
        store = Store.query.filter_by(user_id=user.id).first()
        
        if not store:
            print("No store found for DICCESS. Creating one...")
            store = Store(
                user_id=user.id,
                name="DICCESS Store",
                slug="diccess-store",
                credit_balance=0.0
            )
            db.session.add(store)
        
        # Add Credit
        store.credit_balance += 10.0
        db.session.commit()
        
        print(f"Added GHc 10.00 to store '{store.name}'. New Balance: {store.credit_balance}")

if __name__ == "__main__":
    add_credit()
