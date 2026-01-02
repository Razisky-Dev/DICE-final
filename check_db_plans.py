from app import app, db, DataPlan

with app.app_context():
    plans = DataPlan.query.all()
    print(f"Total Plans: {len(plans)}")
    for p in plans:
        print(f"Network: {p.network}, Size: {p.plan_size}")
