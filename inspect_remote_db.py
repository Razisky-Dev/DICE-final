import sqlite3
import os

# Connect to the instance/dice.db as that is likely the production DB path relative to root
db_path = 'instance/dice.db'

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}, trying dice.db")
    db_path = 'dice.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== STORE Table Columns ===")
    cursor.execute("PRAGMA table_info(store)")
    for col in cursor.fetchall():
        print(col)

    print("\n=== ORDER Table Columns ===")
    cursor.execute("PRAGMA table_info(order)")
    for col in cursor.fetchall():
        print(col)

    print("\n=== TRANSACTION Table Columns ===")
    cursor.execute("PRAGMA table_info(transaction)")
    for col in cursor.fetchall():
        print(col)

    conn.close()
except Exception as e:
    print(f"Error: {e}")
