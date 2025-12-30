from app import app, db
from sqlalchemy import text

print("Updating Store table with 'notice' column...")

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE store ADD COLUMN notice VARCHAR(500)"))
            conn.commit()
        print("Column 'notice' added successfully.")
    except Exception as e:
        print(f"Error (column might already exist): {e}")
