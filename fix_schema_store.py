
import sqlite3
import os
import glob
from app import app, db

def fix_db(db_path):
    print(f"\n>>> Checking DB: {db_path}")
    if not os.path.exists(db_path):
        print("    File does not exist.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # STORE TABLE
        cursor.execute("PRAGMA table_info(store)")
        store_cols = [row[1] for row in cursor.fetchall()]
        
        if 'status' not in store_cols:
            print("  [Store] Adding 'status' column...")
            try:
                cursor.execute("ALTER TABLE store ADD COLUMN status TEXT DEFAULT 'Active'")
                conn.commit()
                print("  [Store] 'status' added.")
            except Exception as e:
                print(f"    Error: {e}")
        else:
            print("  [Store] 'status' already exists.")
            
        conn.close()

    except Exception as e:
        print(f"Failed to process {db_path}: {e}")

def main():
    with app.app_context():
        # Identify Active DB
        if db.engine.url.database:
            active_db = os.path.abspath(db.engine.url.database)
            fix_db(active_db)
        
        # Check others
        db_files = glob.glob('**/*.db', recursive=True)
        for db_file in db_files:
            abs_path = os.path.abspath(db_file)
            if db.engine.url.database and abs_path != os.path.abspath(db.engine.url.database):
                fix_db(abs_path)

if __name__ == "__main__":
    main()
