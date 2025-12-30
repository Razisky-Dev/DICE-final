from app import app, db
from sqlalchemy import text

print("Updating StoreOrder table with new columns...")

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE store_order ADD COLUMN email VARCHAR(120)"))
            conn.execute(text("ALTER TABLE store_order ADD COLUMN network VARCHAR(20)"))
            conn.commit()
        print("Columns 'email' and 'network' added successfully.")
    except Exception as e:
        print(f"Error (cols might exist): {e}")
