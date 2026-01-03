from app import app, db
from sqlalchemy import text

def update_schema():
    with app.app_context():
        columns = [
            ("recipient_number", "VARCHAR(20)"),
            ("recipient_network", "VARCHAR(20)"),
            ("account_name", "VARCHAR(100)")
        ]
        
        for col, col_type in columns:
            try:
                # Check if exists (SQLite specific check or just try/except)
                # We'll just try adding it
                db.session.execute(text(f"ALTER TABLE transaction ADD COLUMN {col} {col_type}"))
                print(f"Added column {col}")
            except Exception as e:
                print(f"Column {col} might already exist or error: {e}")
                
        db.session.commit()
        print("Schema update completed.")

if __name__ == "__main__":
    update_schema()
