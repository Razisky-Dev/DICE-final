
import sys
from app import app, db, User, Store

def manage_credit():
    print("=== Manual Store Credit Manager ===")
    
    with app.app_context():
        email = input("Enter user email: ").strip()
        user = User.query.filter_by(email=email).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found.")
            return

        if not user.store:
            print(f"❌ User '{user.username}' does not have a store setup.")
            return
            
        print(f"\nUser: {user.username} ({user.email})")
        print(f"Current Store Credit: GH₵ {user.store.credit_balance:,.2f}")
        
        try:
            amount_str = input("\nEnter amount to ADD to credit (use negative to subtract): ").strip()
            amount = float(amount_str)
            
            user.store.credit_balance += amount
            db.session.commit()
            
            print(f"\n✅ Success! Added GH₵{amount:,.2f}")
            print(f"New Store Credit: GH₵ {user.store.credit_balance:,.2f}")
            
        except ValueError:
            print("❌ Invalid amount entered.")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    manage_credit()
