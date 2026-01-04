import os
from jinja2 import Environment, FileSystemLoader

template_dir = 'templates'
env = Environment(loader=FileSystemLoader(template_dir))

def check_templates(directory):
    with open('template_check_results.txt', 'w') as log:
        log.write(f"Checking templates in {directory}...\n")
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    rel_path = os.path.relpath(os.path.join(root, file), template_dir)
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            env.parse(f.read())
                        log.write(f"OK: {rel_path}\n")
                    except Exception as e:
                        log.write(f"ERROR: {rel_path} -> {e}\n")
                        print(f"ERROR: {rel_path} -> {e}")


check_templates(template_dir)
