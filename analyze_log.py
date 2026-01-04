import re

log_file = 'local_dice_err.txt'

try:
    with open(log_file, 'r', encoding='utf-16') as f:
        content = f.read()
except UnicodeError:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

# Split into lines
lines = content.splitlines()

# Find occurrences of "TemplateSyntaxError"
matches = []
for i, line in enumerate(lines):
    if "TemplateSyntaxError" in line:
        # Get context: 10 lines before and 5 lines after
        start = max(0, i - 10)
        end = min(len(lines), i + 5)
        matches.append("\n".join(lines[start:end]))

if matches:
    print(f"Found {len(matches)} occurrences. Showing the last one:")
    print(matches[-1])
else:
    print("No TemplateSyntaxError found.")
