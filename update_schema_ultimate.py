import sqlite3
import os

def fix_db(db_path):
    print(f"Checking DB: {db_path}")
    if not os.path.exists(db_path):
        print("  DB not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. STORE TABLE
        print("Checking STORE table...")
        cursor.execute("PRAGMA table_info(store)")
        cols = [row[1] for row in cursor.fetchall()]
        
        updates = {
            'status': "TEXT DEFAULT 'Active'",
            'total_sales': "FLOAT DEFAULT 0.0",
            'total_withdrawn': "FLOAT DEFAULT 0.0",
            'credit_balance': "FLOAT DEFAULT 0.0" # Critical for store view
        }
        
        for col, type_def in updates.items():
            if col not in cols:
                print(f"  Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE store ADD COLUMN {col} {type_def}")
                    conn.commit()
                except Exception as e:
                    print(f"  Error adding {col}: {e}")

        # 2. ORDER TABLE
        print("Checking ORDER table...")
        cursor.execute("PRAGMA table_info(order)") # Note: SQLAlchemy might use 'order' or 'orders'? Flask-SQLAlchemy usually 'order' if model is Order.
        # But 'order' is a reserved keyword in SQL. SQLAlchemy often quotes it or uses 'order'. 
        # Let's check table list first.
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        target_table = 'order' if 'order' in tables else 'orders' # Fallback
        
        if target_table in tables:
            cursor.execute(f"PRAGMA table_info(\"{target_table}\")") # Quote for safety
            cols = [row[1] for row in cursor.fetchall()]
            
            # Check for any potentially missing columns based on templates
            # e.g. commission? (Only in StoreOrder)
            # Order model has: transaction_id, network, package, phone, amount, status, date...
            # Inspecting app.py code, these seem standard.
            pass
        
        conn.close()
        print("Done.")

    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    # Try common paths
    paths = ['instance/dice.db', 'dice.db', '/var/www/dice/instance/dice.db']
    for p in paths:
        fix_db(p)
