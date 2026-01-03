#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, User, db

def capture_admin_orders():
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(email='admin@razilhub.com').first()
        
        if not admin:
            print("Admin user not found!")
            return
            
        print(f"=== CAPTURING ADMIN ORDERS PAGE ===")
        print(f"User: {admin.username} ({admin.email})")
        print(f"Is Admin: {admin.is_admin}")
        print()
        
        # Simulate login and capture the page
        with app.test_client() as client:
            # Simulate login session
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin.id)
                sess['_fresh'] = True
            
            # Get the admin orders page
            response = client.get('/admin/orders')
            
            if response.status_code == 200:
                content = response.data.decode('utf-8')
                
                # Save the full HTML
                with open('admin_orders_captured.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("Successfully captured admin orders page")
                print(f"Page saved to: admin_orders_captured.html")
                print(f"Content length: {len(content)} characters")
                print()
                
                # Analyze the content
                button_count = content.count('data-bs-toggle="modal"')
                modal_count = content.count('id="updateStatusModal')
                export_link_count = content.count('Export CSV')
                
                print("=== ANALYSIS ===")
                print(f"Modal buttons found: {button_count}")
                print(f"Modals found: {modal_count}")
                print(f"Export CSV links: {export_link_count}")
                print()
                
                # Extract key sections
                if 'class="table-responsive"' in content:
                    print("Table section found")
                else:
                    print("Table section missing")
                    
                if 'custom modal system' in content.lower():
                    print("Custom modal JavaScript found")
                else:
                    print("Custom modal JavaScript missing")
                
                # Show sample of button HTML
                if 'data-bs-toggle="modal"' in content:
                    import re
                    button_match = re.search(r'<button[^>]*data-bs-toggle="modal"[^>]*>.*?</button>', content, re.DOTALL)
                    if button_match:
                        print("\n=== SAMPLE BUTTON HTML ===")
                        print(button_match.group(0))
                        print()
                
                # Show sample of modal HTML
                if 'id="updateStatusModal' in content:
                    modal_match = re.search(r'<div[^>]*id="updateStatusModal[^"]*"[^>]*>.*?</div>.*?</div>.*?</div>', content, re.DOTALL)
                    if modal_match:
                        print("=== SAMPLE MODAL HTML ===")
                        print(modal_match.group(0)[:500] + "...")
                        print()
                
                print("=== NEXT STEPS ===")
                print("1. Open 'admin_orders_captured.html' in your browser")
                print("2. Check if buttons and modals are visible")
                print("3. Test clicking buttons in the captured page")
                print("4. Look for any JavaScript errors in browser console")
                
            else:
                print(f"Failed to get admin orders page: {response.status_code}")

if __name__ == "__main__":
    capture_admin_orders()
