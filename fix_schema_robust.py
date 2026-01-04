
import sqlite3
import os
import glob

def fix_db(db_path):
    print(f"Checking DB: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # List of columns to check/add
        new_cols = {
            'is_suspended': 'BOOLEAN DEFAULT 0',
            'is_super_admin': 'BOOLEAN DEFAULT 0',
            'last_read_notice_timestamp': 'TIMESTAMP',
            'preferred_network': 'TEXT'
        }
        
        for col, type_def in new_cols.items():
            if col not in columns:
                print(f"  + Adding {col}...")
                try:
                    cursor.execute(f"ALTER TABLE user ADD COLUMN {col} {type_def}")
                    conn.commit()
                except Exception as e:
                    print(f"    Error adding {col}: {e}")
            else:
                print(f"  = {col} exists.")
                
        conn.close()
    except Exception as e:
        print(f"Failed to open {db_path}: {e}")

def main():
    # Find all .db files
    db_files = glob.glob('**/*.db', recursive=True)
    print(f"Found {len(db_files)} databases: {db_files}")
    
    for db_file in db_files:
        fix_db(db_file)

if __name__ == "__main__":
    main()
