from app import app, db

def update_database():
    """
    Creates any missing database tables defined in the SQLAlchemy models.
    This is necessary because Gunicorn does not run the `if __name__ == '__main__': db.create_all()` block.
    """
    print("Connecting to database...")
    with app.app_context():
        print("Creating all missing tables...")
        db.create_all()
        print("Database structure updated successfully!")

if __name__ == "__main__":
    update_database()
