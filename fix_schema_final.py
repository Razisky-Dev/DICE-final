
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
        
        # 1. USER TABLE
        cursor.execute("PRAGMA table_info(user)")
        user_cols = [row[1] for row in cursor.fetchall()]
        user_updates = {
            'is_suspended': 'BOOLEAN DEFAULT 0',
            'is_super_admin': 'BOOLEAN DEFAULT 0',
            'last_read_notice_timestamp': 'TIMESTAMP',
            'preferred_network': 'TEXT'
        }
        for col, type_def in user_updates.items():
            if col not in user_cols:
                print(f"  [User] Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {col} {type_def}")
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"  [User] {col} OK.")

        # 2. DATA_PLAN TABLE
        cursor.execute("PRAGMA table_info(data_plan)")
        plan_cols = [row[1] for row in cursor.fetchall()]
        plan_updates = {
            'manufacturing_price': 'FLOAT DEFAULT 0.0',
            'dealer_price': 'FLOAT DEFAULT 0.0'
        }
        for col, type_def in plan_updates.items():
            if col not in plan_cols:
                print(f"  [DataPlan] Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE data_plan ADD COLUMN {col} {type_def}")
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"  [DataPlan] {col} OK.")

        # 3. TRANSACTION TABLE
        cursor.execute("PRAGMA table_info('transaction')") # Quote keyword
        txn_cols = [row[1] for row in cursor.fetchall()]
        txn_updates = {
            'recipient_number': 'TEXT',
            'recipient_network': 'TEXT',
            'account_name': 'TEXT'
        }
        for col, type_def in txn_updates.items():
            if col not in txn_cols:
                print(f"  [Transaction] Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE `transaction` ADD COLUMN {col} {type_def}")
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"  [Transaction] {col} OK.")

        # 4. STORE TABLE
        cursor.execute("PRAGMA table_info(store)")
        store_cols = [row[1] for row in cursor.fetchall()]
        store_updates = {
            'whatsapp_group_link': 'TEXT',
            'notice': 'TEXT',
            'slug': 'TEXT'
        }
        for col, type_def in store_updates.items():
            if col not in store_cols:
                print(f"  [Store] Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE store ADD COLUMN {col} {type_def}")
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"  [Store] {col} OK.")

        # 5. STORE_ORDER TABLE
        cursor.execute("PRAGMA table_info(store_order)")
        so_cols = [row[1] for row in cursor.fetchall()]
        so_updates = {
            'email': 'TEXT',
            'network': 'TEXT'
        }
        for col, type_def in so_updates.items():
            if col not in so_cols:
                print(f"  [StoreOrder] Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE store_order ADD COLUMN {col} {type_def}")
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"  [StoreOrder] {col} OK.")
        
        conn.commit()
        conn.close()
        print("  Database updated successfully.")

    except Exception as e:
        print(f"Failed to process {db_path}: {e}")

def main():
    with app.app_context():
        # Identify Active DB
        active_db = None
        if db.engine.url.database:
            active_db = os.path.abspath(db.engine.url.database)
            print(f"Active App Database: {active_db}")
            fix_db(active_db)
        
        # Check others just in case
        db_files = glob.glob('**/*.db', recursive=True)
        for db_file in db_files:
            abs_path = os.path.abspath(db_file)
            if abs_path != active_db:
                print(f"Checking other DB: {abs_path}")
                fix_db(abs_path)

if __name__ == "__main__":
    main()
