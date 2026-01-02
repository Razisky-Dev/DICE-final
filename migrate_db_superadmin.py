from app import app, db
from sqlalchemy import text

def add_super_admin_column():
    with app.app_context():
        # Check if column exists
        with db.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(user)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_super_admin' not in columns:
                print("Adding is_super_admin column to user table...")
                conn.execute(text("ALTER TABLE user ADD COLUMN is_super_admin BOOLEAN DEFAULT 0"))
                conn.commit()
                print("Column added successfully.")
            else:
                print("Column is_super_admin already exists.")

if __name__ == "__main__":
    add_super_admin_column()
