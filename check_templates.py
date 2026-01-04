import os
from jinja2 import Environment, FileSystemLoader

template_dir = 'templates'
env = Environment(loader=FileSystemLoader(template_dir))

def check_templates(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        env.parse(f.read())
                    # print(f"OK: {rel_path}")
                except Exception as e:
                    print(f"ERROR in {rel_path}: {e}")

print("Checking templates...")
check_templates(template_dir)

# Also check likely standalone templates in root if any (though usually not rendered directly)
# admin_orders_captured.html was seen in root.
try:
    with open('admin_orders_captured.html', 'r', encoding='utf-8') as f:
        env = Environment(loader=FileSystemLoader('.'))
        env.parse(f.read())
except Exception as e:
    print(f"ERROR in admin_orders_captured.html: {e}")
