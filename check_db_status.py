
import os
import sys
from app import app, db
from sqlalchemy import text

def check():
    with open("db_check_result.txt", "w") as f:
        f.write(f"CWD: {os.getcwd()}\n")
        try:
            f.write(f"ls /var/www/dice: {os.listdir('/var/www/dice')}\n")
        except:
            pass
        try:
            f.write(f"ls /var/www/dice/instance: {os.listdir('/var/www/dice/instance')}\n")
        except:
            pass
            
        with app.app_context():
            uri = app.config['SQLALCHEMY_DATABASE_URI']
            f.write(f"DB URI: {uri}\n")
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("PRAGMA table_info(data_plan)"))
                    columns = [row for row in result]
                    f.write("Columns:\n")
                    for col in columns:
                        f.write(f"{col}\n")
            except Exception as e:
                f.write(f"DB Error: {e}\n")

if __name__ == "__main__":
    check()
