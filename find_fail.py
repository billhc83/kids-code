import re

with open('admin_fail_final.txt', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    match = re.search(r'Request:\s*\nE\s*-\s*GET\s+(.*)', content)
    if match:
        print("FAILING REQUEST:", match.group(1))
    else:
        print("No failing request found in logs.")
