
import sqlite3
import os

DB_PATH = 'instance/database.db'

def fix_schema():
    print(f"Checking schema at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(user)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'is_suspended' not in columns:
        print("Adding is_suspended column...")
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN is_suspended BOOLEAN DEFAULT 0")
            conn.commit()
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Column is_suspended already exists.")

    # Check for other potentially missing columns from recent updates
    if 'is_super_admin' not in columns:
        print("Adding is_super_admin column...")
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN is_super_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("Done.")
        except Exception as e:
            print(f"Error: {e}")

    if 'last_read_notice_timestamp' not in columns:
        print("Adding last_read_notice_timestamp column...")
        try:
             # DateTime usually stored as TEXT or REAL in sqlite if not using adapters, but here we just add column
             cursor.execute("ALTER TABLE user ADD COLUMN last_read_notice_timestamp TIMESTAMP")
             conn.commit()
             print("Done.")
        except Exception as e:
             print(f"Error: {e}")

    if 'preferred_network' not in columns:
         print("Adding preferred_network column...")
         try:
             cursor.execute("ALTER TABLE user ADD COLUMN preferred_network TEXT")
             conn.commit()
             print("Done.")
         except Exception as e:
             print(f"Error: {e}")

    conn.close()

if __name__ == "__main__":
    fix_schema()
