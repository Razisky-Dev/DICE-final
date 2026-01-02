
import sqlite3
import os

# Define the database path
DB_PATH = '/var/www/dice/instance/database.db'

def add_phone_column():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(order)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'phone' not in columns:
            print("Adding 'phone' column to 'order' table...")
            # SQLite supports adding columns with ALTER TABLE
            cursor.execute('ALTER TABLE "order" ADD COLUMN phone TEXT')
            conn.commit()
            print("Migration successful.")
        else:
            print("'phone' column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    add_phone_column()
