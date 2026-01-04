
import os
from app import app, db
from sqlalchemy import text

def debug_db():
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"App Config URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        # Get the actual file path from the engine
        url = db.engine.url
        print(f"Engine URL: {url}")
        print(f"Database File: {url.database}")
        
        # Check if file exists
        if url.database and os.path.exists(url.database):
            print(f"Database file exists at: {os.path.abspath(url.database)}")
        else:
            print("Database file NOT found at expected path.")
            
        # Try to run the query that failed
        try:
            print("Checking query...")
            result = db.session.execute(text("SELECT recipient_number FROM `transaction` LIMIT 1"))
            print("Column recipient_number EXISTS.")
        except Exception as e:
            print(f"Column recipient_number MISSING. Error: {e}")

if __name__ == "__main__":
    debug_db()
