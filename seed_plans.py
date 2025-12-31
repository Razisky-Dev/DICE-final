
from app import app, db, DataPlan, DEALER_PACKAGES

def seed_data_plans():
    with app.app_context():
        # Create table if not exists
        db.create_all()
        
        print("Seeding Data Plans...")
        
        # 1. MTN
        count = 0
        for pkg in DEALER_PACKAGES["MTN"]:
            # Check if exists
            exists = DataPlan.query.filter_by(network="MTN", plan_size=pkg["package"]).first()
            if not exists:
                new_plan = DataPlan(
                    network="MTN",
                    plan_size=pkg["package"],
                    # For now, assuming cost = price - 0.5 (just an estimation for seeding) 
                    # OR just set cost = selling price initially and let admin update
                    cost_price=pkg["price"], 
                    selling_price=pkg["price"],
                    display_order=count
                )
                db.session.add(new_plan)
                count += 1
        
        # Seed placeholders for others if empty
        if not DataPlan.query.filter_by(network="TELECEL").first():
             telecel_plans = [("1 GB", 5.0), ("2 GB", 10.0)]
             for idx, (size, price) in enumerate(telecel_plans):
                 db.session.add(DataPlan(network="TELECEL", plan_size=size, cost_price=price, selling_price=price, display_order=idx))

        if not DataPlan.query.filter_by(network="AIRTELTIGO").first():
             at_plans = [("Big Time 1 GB", 4.5), ("Big Time 2 GB", 9.0)]
             for idx, (size, price) in enumerate(at_plans):
                 db.session.add(DataPlan(network="AIRTELTIGO", plan_size=size, cost_price=price, selling_price=price, display_order=idx))

        db.session.commit()
        print("Data Plans Seeded Successfully!")

if __name__ == "__main__":
    seed_data_plans()
