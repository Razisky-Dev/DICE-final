import sqlite3
import os
import sys

def fix_file(db_path):
    print(f"Checking {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. STORE TABLE
        try:
            cursor.execute("PRAGMA table_info(store)")
            columns = [col[1] for col in cursor.fetchall()]
            
            needed_columns = {
                'status': "TEXT DEFAULT 'Active'",
                'total_sales': "FLOAT DEFAULT 0.0",
                'total_withdrawn': "FLOAT DEFAULT 0.0",
                'credit_balance': "FLOAT DEFAULT 0.0"
            }
            
            for col, definition in needed_columns.items():
                if col not in columns:
                    print(f"  [STORE] Adding {col}...")
                    cursor.execute(f"ALTER TABLE store ADD COLUMN {col} {definition}")
        except Exception as e:
            print(f"  [STORE] Error: {e}")

        # 2. TRANSACTION TABLE
        try:
             cursor.execute("PRAGMA table_info(\"transaction\")") # Quoted
             txn_cols = [col[1] for col in cursor.fetchall()]
             
             if 'account_name' not in txn_cols:
                  print("  [txn] Adding account_name...")
                  cursor.execute("ALTER TABLE `transaction` ADD COLUMN account_name TEXT")
             
             if 'recipient_network' not in txn_cols:
                  print("  [txn] Adding recipient_network...")
                  cursor.execute("ALTER TABLE `transaction` ADD COLUMN recipient_network TEXT")
        except Exception as e:
            print(f"  [txn] Error: {e}")
            
        conn.commit()
        conn.close()
        print(f"  Done with {db_path}.")
    except Exception as e:
        print(f"  Failed to open {db_path}: {e}")

def main():
    print("Starting Ultimate DB Fixer...")
    
    # List of candidates to try
    candidates = [
        'database.db',
        'instance/database.db',
        'dice.db',
        'instance/dice.db',
        '/var/www/dice/database.db',
        '/var/www/dice/instance/database.db'
    ]
    
    found = False
    for path in candidates:
        if os.path.exists(path):
            fix_file(path)
            found = True
            
    if not found:
        print("WARNING: No database files found in standard locations.")
        # Try finding any .db file
        import glob
        for f in glob.glob("**/*.db", recursive=True):
             fix_file(f)

if __name__ == "__main__":
    main()
