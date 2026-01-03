#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, User, db
from werkzeug.security import check_password_hash

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
            if check_password_hash(admin.password, 'admin123'):
                print("Password verification SUCCESSFUL")
                print("Login credentials are correct!")
                
                # Now test the orders page
                with app.test_client() as client:
                    # Simulate login
                    with client.session_transaction() as sess:
                        sess['_user_id'] = str(admin.id)
                        sess['_fresh'] = True
                    
                    # Test orders page
                    response = client.get('/admin/orders')
                    print(f"Orders page status: {response.status_code}")
                    
                    if response.status_code == 200:
                        content = response.data.decode('utf-8')
                        button_count = content.count('data-bs-toggle="modal"')
                        modal_count = content.count('id="updateStatusModal')
                        print(f"Buttons found: {button_count}")
                        print(f"Modals found: {modal_count}")
                        
                        if button_count > 0 and modal_count > 0:
                            print("Template rendering correctly with buttons and modals")
                        else:
                            print("Template missing buttons or modals")
                    else:
                        print("Failed to load orders page")
                        
            else:
                print("Password verification FAILED")
                
        else:
            print("Admin user not found with email admin@razilhub.com")

if __name__ == "__main__":
    test_admin_login()
