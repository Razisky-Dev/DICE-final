from app import app, db, User, Transaction
from datetime import datetime

def create_test_withdrawal():
    with app.app_context():
        # Get Admin User
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            print("Admin user not found!")
            return

        # Prepare dummy withdrawal
        ref = f"WTH|MTN|0244000001|Test Verification|{int(datetime.utcnow().timestamp())}"
        
        txn = Transaction(
            user_id=admin.id,
            reference=ref,
            type="Withdrawal",
            amount=1.00,
            status="Pending"
        )
        
        db.session.add(txn)
        db.session.commit()
        print(f"Created pending withdrawal for {admin.username}. Ref: {ref}")

if __name__ == "__main__":
    create_test_withdrawal()
