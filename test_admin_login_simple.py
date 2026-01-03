#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, User, db

def test_admin_login():
    with app.app_context():
        # Check if admin user exists with that email
        admin = User.query.filter_by(email='admin@razilhub.com').first()
        
        if admin:
            print(f"Admin user found: {admin.username}")
            print(f"Email: {admin.email}")
            print(f"Is admin: {admin.is_admin}")
            print(f"Is super admin: {admin.is_super_admin}")
            
            # Test password
            if admin.check_password('admin123'):
                print("Password verification successful")
            else:
                print("Password verification failed")
                
        else:
            print("Admin user not found with email admin@razilhub.com")
            
            # Check if admin user exists with username 'admin'
            admin_by_username = User.query.filter_by(username='admin').first()
            if admin_by_username:
                print(f"Found admin by username: {admin_by_username.email}")
                print("Consider using username 'admin' for login instead")

if __name__ == "__main__":
    test_admin_login()
