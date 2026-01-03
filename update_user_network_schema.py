from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Check if column exists
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT preferred_network FROM user LIMIT 1"))
            print("Column 'preferred_network' already exists.")
        except:
            print("Adding 'preferred_network' column to 'user' table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN preferred_network VARCHAR(20)"))
            print("Migration successful: Added 'preferred_network'.")

if __name__ == "__main__":
    migrate()
