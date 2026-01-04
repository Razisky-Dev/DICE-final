import sqlite3
import os
import sys

def fix_db():
    print("Starting DB Fix...")
    
    # Try multiple possible paths for the database
    possible_paths = [
        os.path.join(os.getcwd(), 'instance', 'dice.db'),
        os.path.join(os.getcwd(), 'dice.db'),
        '/var/www/dice/instance/dice.db'
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
            
    if not db_path:
        print("ERROR: Could not find dice.db")
        return

    print(f"Using Database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Fix STORE Table
        cursor.execute("PRAGMA table_info(store)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Store Columns: {columns}")
        
        needed_columns = {
            'status': "TEXT DEFAULT 'Active'",
            'total_sales': "FLOAT DEFAULT 0.0",
            'total_withdrawn': "FLOAT DEFAULT 0.0",
            'credit_balance': "FLOAT DEFAULT 0.0"
        }
        
        for col, definition in needed_columns.items():
            if col not in columns:
                print(f"Adding missing column: {col}")
                try:
                    cursor.execute(f"ALTER TABLE store ADD COLUMN {col} {definition}")
                    print(f" - Added {col}")
                except Exception as e:
                    print(f" - Failed to add {col}: {e}")
            else:
                print(f" - {col} exists")

        # 2. Fix Transaction 'account_name' if missing (Common issue)
        cursor.execute("PRAGMA table_info(transaction)")
        txn_cols = [col[1] for col in cursor.fetchall()]
        
        if 'account_name' not in txn_cols:
             print("Adding account_name to transaction...")
             cursor.execute("ALTER TABLE `transaction` ADD COLUMN account_name TEXT")
             
        if 'recipient_network' not in txn_cols:
             print("Adding recipient_network to transaction...")
             cursor.execute("ALTER TABLE `transaction` ADD COLUMN recipient_network TEXT")

        conn.commit()
        conn.close()
        print("Database Fix Completed Successfully.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    fix_db()
