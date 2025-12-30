from app import app, db
from sqlalchemy import text

print("Updating User table with 'is_suspended' column...")

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE user ADD COLUMN is_suspended BOOLEAN DEFAULT 0"))
            conn.commit()
        print("Column 'is_suspended' added successfully.")
    except Exception as e:
        print(f"Column update error (might already exist): {e}")
