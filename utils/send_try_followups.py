#!/usr/bin/env python3
"""
Standalone weekly follow-up script — run manually or via cron.

One reminder per lead, ever (not a drip sequence). Leads who converted on
their own before this ran are stamped followed_up_at without an email being
sent, so they're never picked up again either.

Usage:
    python utils/send_try_followups.py

Cron example (Monday mornings at 9am), same convention as
utils/purge_deleted_accounts.py:
    0 9 * * 1 cd /path/to/project && venv/bin/python utils/send_try_followups.py >> logs/try_followups.log 2>&1
"""

import sys
import os
import datetime
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config import RESEND_API_KEY
from utils.leads import get_unfollowed_leads, email_exists_in_users, mark_followed_up


def send_followup_email(to_email):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": "KidsCode <no-reply@kidscode.ca>",
            "to": to_email,
            "subject": "Still thinking about KidsCode?",
            "html": """
                <h2>Hey there!</h2>
                <p>You tried out a KidsCode project a little while ago — thanks for
                giving it a shot!</p>
                <p>If you're ready to keep building, head back to
                <a href="https://app.kidscode.ca/try">app.kidscode.ca/try</a> any time.</p>
            """
        }
    )
    if not resp.ok:
        print(f"[send_followup_email] Resend error {resp.status_code}: {resp.text}")
    return resp.ok


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Starting weekly try-page follow-up run")

    unfollowed = get_unfollowed_leads()
    if not unfollowed:
        print(f"[{now}] No unfollowed leads.")
        return

    sent = 0
    skipped_converted = 0
    errors = 0
    for lead in unfollowed:
        try:
            if email_exists_in_users(lead["email"]):
                mark_followed_up(lead["id"])
                skipped_converted += 1
                continue
            ok = send_followup_email(lead["email"])
            mark_followed_up(lead["id"])
            if ok:
                sent += 1
            else:
                errors += 1
        except Exception as e:
            print(f"  ERROR processing lead {lead.get('id')}: {e}")
            errors += 1

    print(f"[{now}] Done. Sent: {sent}, Skipped (already converted): {skipped_converted}, Errors: {errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
