from app import app, db
from sqlalchemy import text

print("Updating User table with 'last_read_notice_timestamp' column...")

with app.app_context():
    try:
        with db.engine.connect() as conn:
            # Check if column exists first to avoid error (sqlite doesn't support IF NOT EXISTS for columns easily in raw SQL)
            # But simple ADD COLUMN is safe enough if we catch the operational error
            conn.execute(text("ALTER TABLE user ADD COLUMN last_read_notice_timestamp DATETIME"))
            conn.commit()
        print("Column 'last_read_notice_timestamp' added successfully.")
    except Exception as e:
        print(f"Column update error (might already exist): {e}")
