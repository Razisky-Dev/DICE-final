from app import app, db
from sqlalchemy import text, inspect

with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('user')]
    
    if 'last_read_notice_timestamp' not in columns:
        print("Migrating: Adding last_read_notice_timestamp to User table...")
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE user ADD COLUMN last_read_notice_timestamp DATETIME"))
            conn.commit()
        print("Migration successful: Column added.")
    else:
        print("Migration checked: Column already exists.")
