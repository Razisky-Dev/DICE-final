
from app import app, db
from sqlalchemy import text

def add_manufacturing_price_column():
    with app.app_context():
        try:
            # 1. Add manufacturing_price column
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE data_plan ADD COLUMN manufacturing_price FLOAT DEFAULT 0.0"))
                conn.commit()
            print("Successfully added 'manufacturing_price' column to 'data_plan' table.")
        except Exception as e:
            print(f"Error (might already exist): {e}")

if __name__ == "__main__":
    add_manufacturing_price_column()
