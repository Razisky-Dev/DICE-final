
from app import app, db
from sqlalchemy import text

def add_manufacturing_price_column():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if column exists first to avoid error if partial run
                result = conn.execute(text("PRAGMA table_info(data_plan)"))
                columns = [row[1] for row in result]
                if 'manufacturing_price' not in columns:
                    conn.execute(text("ALTER TABLE data_plan ADD COLUMN manufacturing_price FLOAT DEFAULT 0.0"))
                    conn.commit()
                    print("Successfully added 'manufacturing_price' column.")
                else:
                    print("'manufacturing_price' column already exists.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    add_manufacturing_price_column()
