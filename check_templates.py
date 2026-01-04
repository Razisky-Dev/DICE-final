import os
from jinja2 import Environment, FileSystemLoader

template_dir = 'templates'
env = Environment(loader=FileSystemLoader(template_dir))

def check_templates(directory):
    print(f"Checking templates in {directory}...")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                try:
                    # We need to simulate the 'admin/base.html' extension if it's an admin file
                    # easiest way is to just parse it. Jinja2 environment.parse() checks syntax without rendering.
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        env.parse(f.read())
                    # print(f"OK: {rel_path}")
                except Exception as e:
                    print(f"ERROR in {rel_path}: {e}")

check_templates(template_dir)
