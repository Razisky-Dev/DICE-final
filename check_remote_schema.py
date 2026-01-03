from app import app, db
from sqlalchemy import inspect

def check_schema():
    with app.app_context():
        inspector = inspect(db.engine)
        for table_name in ['order', 'user']:
            print(f"Table: {table_name}")
            columns = inspector.get_columns(table_name)
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")


if __name__ == "__main__":
    check_schema()
