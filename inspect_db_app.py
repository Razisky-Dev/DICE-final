from app import app, db
from sqlalchemy import inspect

def inspect_db():
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("=== STORE Table ===")
        try:
           cols = [c['name'] for c in inspector.get_columns('store')]
           print(cols)
        except Exception as e:
           print(f"Error: {e}")

        print("\n=== ORDER Table ===")
        try:
           cols = [c['name'] for c in inspector.get_columns('order')]
           print(cols)
        except Exception as e:
           print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
