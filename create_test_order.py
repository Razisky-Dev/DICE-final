from app import app, db, User, Order, DataPlan
from datetime import datetime
import random

def create_test_order():
    with app.app_context():
        # Get a user (not admin)
        user = User.query.filter_by(is_admin=False).first()
        if not user:
            print("No regular user found. Creating one...")
            user = User(
                username="testuser",
                email="test@example.com",
                password="hashedprob", # In reality, use hash
                first_name="Test",
                last_name="User",
                balance=100.0
            )
            db.session.add(user)
            db.session.commit()

        # Create Order
        ref_id = f"TEST-{random.randint(1000, 9999)}"
        new_order = Order(
            transaction_id=ref_id,
            user_id=user.id,
            network="MTN",
            package="1GB",
            phone="0540000000",
            amount=4.5,
            status="Pending",
            date=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.commit()
        print(f"Test Order Created: #{new_order.id} for {user.username} (Ref: {ref_id})")

if __name__ == "__main__":
    create_test_order()
