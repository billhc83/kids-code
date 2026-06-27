#!/usr/bin/env python3
"""
Standalone purge script — run manually or via cron.

Usage:
    python utils/purge_deleted_accounts.py

Cron example (daily at 2am):
    0 2 * * * cd /path/to/project && venv/bin/python utils/purge_deleted_accounts.py >> logs/purge.log 2>&1
"""

import sys
import os
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from utils.deletion import get_accounts_due_for_purge, purge_user

def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Starting account purge run")

    accounts = get_accounts_due_for_purge()
    if not accounts:
        print(f"[{now}] No accounts due for purge.")
        return

    print(f"[{now}] Accounts to purge: {len(accounts)}")
    purged = 0
    errors = 0
    for account in accounts:
        try:
            purge_user(account["id"], account["username"])
            print(f"  Purged: {account['username']} (requested: {account['deletion_requested_at'][:10]})")
            purged += 1
        except Exception as e:
            print(f"  ERROR purging {account['username']}: {e}")
            errors += 1

    print(f"[{now}] Done. Purged: {purged}, Errors: {errors}")
    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
