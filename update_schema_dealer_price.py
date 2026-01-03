from app import app, db
from sqlalchemy import text

def update_schema():
    with app.app_context():
        # Check if column exists
        try:
            db.session.execute(text("SELECT dealer_price FROM data_plan LIMIT 1"))
            print("Column 'dealer_price' already exists.")
        except:
            print("Adding 'dealer_price' column...")
            try:
                # SQLite ALTER TABLE to add column
                db.session.execute(text("ALTER TABLE data_plan ADD COLUMN dealer_price FLOAT DEFAULT 0.0"))
                db.session.commit()
                print("Column added successfully.")
            except Exception as e:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    update_schema()
