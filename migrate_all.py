import os

migration_scripts = [
    "update_schema_txn_details.py",
    "update_user_schema.py",
    "update_user_network_schema.py",
    "update_store_notice.py",
    "update_schema_manufacturing.py",
    "update_schema_order_phone.py",
    "update_super_admin_schema.py",
    "update_schema_dealer_price.py"
]

print("Starting Consolidated Migration...")

for script in migration_scripts:
    if os.path.exists(script):
        print(f"Running {script}...")
        exit_code = os.system(f"python3 {script}")
        if exit_code != 0:
            print(f"Warning: {script} returned exit code {exit_code}")
    else:
        print(f"Skipping {script}: File not found.")

print("Migration Verification Complete.")
