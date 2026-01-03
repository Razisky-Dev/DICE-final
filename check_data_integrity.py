
from app import app, db
from sqlalchemy import text

def check_data():
    with open("data_integrity.txt", "w") as f:
        with app.app_context():
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT id, network, plan_size, manufacturing_price, dealer_price FROM data_plan"))
                    rows = result.fetchall()
                    f.write(f"Total Rows: {len(rows)}\n")
                    for row in rows:
                        f.write(f"ID: {row[0]}, Net: {row[1]}, Size: {row[2]}, Mfg: {row[3]}, Dlr: {row[4]}\n")
                        if row[3] is None:
                            f.write("  -> WARNING: Manufacturing Price is NULL!\n")
                        if row[4] is None:
                            f.write("  -> WARNING: Dealer Price is NULL!\n")
            except Exception as e:
                f.write(f"Error: {e}\n")

if __name__ == "__main__":
    check_data()
