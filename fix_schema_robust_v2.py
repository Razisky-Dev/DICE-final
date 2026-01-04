
import sqlite3
import os
import glob

def fix_db(db_path):
    print(f"Checking DB: {db_path}")
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

        # 3. TRANSACTION TABLE
        cursor.execute("PRAGMA table_info(transaction)")
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
        
        conn.commit()
        conn.close()
        print("  Database updated.")

    except Exception as e:
        print(f"Failed to process {db_path}: {e}")

def main():
    # Find all .db files
    db_files = glob.glob('**/*.db', recursive=True)
    if not db_files:
        # Fallback to standard location
        if os.path.exists('database.db'): db_files.append('database.db')
        if os.path.exists('instance/database.db'): db_files.append('instance/database.db')
        
    print(f"Found databases: {db_files}")
    
    for db_file in db_files:
        fix_db(db_file)

if __name__ == "__main__":
    main()
