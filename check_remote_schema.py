from app import app, db
from sqlalchemy import inspect

def check_schema():
    with app.app_context():
        inspector = inspect(db.engine)
        for table_name in inspector.get_table_names():
            print(f"Table: {table_name}")
            for column in inspector.get_columns(table_name):
                print(f"  - {column['name']} ({column['type']})")

if __name__ == "__main__":
    check_schema()
