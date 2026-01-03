from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Check if column exists
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT is_super_admin FROM user LIMIT 1"))
            print("Column 'is_super_admin' already exists.")
        except:
            print("Adding 'is_super_admin' column to 'user' table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN is_super_admin BOOLEAN DEFAULT 0"))
            print("Migration successful: Added 'is_super_admin'.")

if __name__ == "__main__":
    migrate()
