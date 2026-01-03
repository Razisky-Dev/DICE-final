#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, Order, db
from flask import url_for

def test_orders_template():
    with app.app_context():
        # Get orders like the admin route does
        page = 1
        per_page = 20
        
        query = Order.query.order_by(Order.date.desc())
        orders = query.paginate(page=page, per_page=per_page)
        
        # Render the template
        with app.test_request_context('/admin/orders'):
            from flask import render_template
            html = render_template('admin/orders.html', orders=orders)
            
            print("=== TEMPLATE ANALYSIS ===")
            print(f"Template rendered successfully: {len(html)} characters")
            
            # Check for modal buttons
            button_count = html.count('data-bs-toggle="modal"')
            print(f"Modal buttons found: {button_count}")
            
            # Check for modals
            modal_count = html.count('class="modal fade"')
            print(f"Modals found: {modal_count}")
            
            # Check for JavaScript
            js_count = html.count('data-bs-toggle="modal"')
            print(f"Button attributes: {js_count}")
            
            # Look for any template errors
            if '{{' in html or '{%' in html:
                print("WARNING: Unrendered template tags found!")
            
            # Check for specific order IDs
            for order in orders.items:
                order_id = f"updateStatusModal{order.id}"
                if order_id in html:
                    print(f"✓ Modal for Order {order.id} found")
                else:
                    print(f"✗ Modal for Order {order.id} MISSING")
            
            # Save HTML for inspection
            with open('orders_debug.html', 'w') as f:
                f.write(html)
            print("Full HTML saved to orders_debug.html")

if __name__ == "__main__":
    test_orders_template()
