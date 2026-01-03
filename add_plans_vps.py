from app import app, db, DataPlan

def add_plans():
    with app.app_context():
        plans = [
            {"network": "MTN", "size": "1GB", "price": 4.5},
            {"network": "TELECEL", "size": "1GB", "price": 5.00},
            {"network": "AIRTELTIGO", "size": "1GB", "price": 6.00}
        ]

        print("--- Adding Data Plans ---")
        for p in plans:
            # Check if exists to avoid duplicates
            existing = DataPlan.query.filter_by(network=p['network'], plan_size=p['size']).first()
            if existing:
                print(f"Updating {p['network']} {p['size']} -> {p['price']}")
                existing.selling_price = p['price']
                # existing.cost_price = p['price'] - 0.5 # Optional assumptions
            else:
                print(f"Creating {p['network']} {p['size']} -> {p['price']}")
                new_plan = DataPlan(
                    network=p['network'],
                    plan_size=p['size'],
                    selling_price=p['price'],
                    cost_price=0.0, # Defaulting cost to 0
                    status='Active'
                )
                db.session.add(new_plan)
        
        try:
            db.session.commit()
            print("Plans added/updated successfully.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_plans()
