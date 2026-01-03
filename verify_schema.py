
import os
from app import app, db
from sqlalchemy import text

def verify():
    with open("schema_verification.txt", "w") as f:
        with app.app_context():
            uri = app.config['SQLALCHEMY_DATABASE_URI']
            f.write(f"DB URI: {uri}\n")
            
            try:
                with db.engine.connect() as conn:
                    # Check DataPlan
                    result = conn.execute(text("PRAGMA table_info(data_plan)"))
                    columns = [row[1] for row in result]
                    f.write(f"DataPlan Columns: {columns}\n")
                    
                    if 'dealer_price' not in columns:
                        f.write("CRITICAL: dealer_price MISSING from data_plan\n")
                    if 'manufacturing_price' not in columns:
                        f.write("CRITICAL: manufacturing_price MISSING from data_plan\n")

                    # Check User
                    result = conn.execute(text("PRAGMA table_info(user)"))
                    columns = [row[1] for row in result]
                    f.write(f"User Columns: {columns}\n")
                    
                    if 'is_super_admin' not in columns:
                        f.write("CRITICAL: is_super_admin MISSING from user\n")
                        
            except Exception as e:
                f.write(f"DB Error: {e}\n")

if __name__ == "__main__":
    verify()
