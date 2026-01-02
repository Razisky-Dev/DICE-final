
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
        
        # List all tables to confirm names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Existing tables: {tables}")

        target_table = None
        if 'order' in tables:
            target_table = 'order'
        elif 'orders' in tables:
             target_table = 'orders'
        
        if not target_table:
            print("Could not find 'order' or 'orders' table.")
            return

        # Check if column exists
        cursor.execute(f'PRAGMA table_info("{target_table}")')
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'phone' not in columns:
            print(f"Adding 'phone' column to '{target_table}' table...")
            # Use strict double quoting for clarity
            try:
                cursor.execute(f'ALTER TABLE "{target_table}" ADD COLUMN phone TEXT')
                conn.commit()
                print("Migration successful.")
            except Exception as e_alter:
                print(f"ALTER failed with double quotes: {e_alter}")
                # Fallback to brackets
                try:
                    print("Retrying with brackets...")
                    cursor.execute(f"ALTER TABLE [{target_table}] ADD COLUMN phone TEXT")
                    conn.commit()
                    print("Migration successful (brackets).")
                except Exception as e_bracket:
                     print(f"ALTER failed with brackets: {e_bracket}")
        else:
            print(f"'phone' column already exists in {target_table}.")
            
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    add_phone_column()
