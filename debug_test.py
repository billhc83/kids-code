with open('admin_debug_s.txt', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'DEBUG: Request made to' in line:
            print(line.strip())
        if 'Request:' in line:
            print("FOUND REQUEST SECTION")
            print(line.strip())
