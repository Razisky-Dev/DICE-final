from app import app, db, DataPlan

def fix_plans():
    with app.app_context():
        # Find plans with "Big Time" in the name
        plans = DataPlan.query.filter(DataPlan.plan_size.like('%Big Time%')).all()
        
        if not plans:
            print("No plans found with 'Big Time'.")
            return

        print(f"Found {len(plans)} plans to fix.")
        
        for plan in plans:
            old_name = plan.plan_size
            new_name = old_name.replace("Big Time ", "").replace("Big Time", "").strip()
            plan.plan_size = new_name
            print(f"Renaming: '{old_name}' -> '{new_name}'")
            
        db.session.commit()
        print("Database updated successfully.")

if __name__ == "__main__":
    fix_plans()
