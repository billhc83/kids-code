"""
utils/leads.py — data access for the `leads` table.

Leads come from the anonymous /try page's email-capture gate (see
routes/try_it.py). Deliberately not part of utils/auth.py: leads are never
`users` rows, and this module has no session/password concerns.
"""

import datetime
from utils.db_client import supabase


def create_lead(email, source="try_page"):
    """Insert a lead row. Returns the inserted row, or None on failure."""
    resp = supabase.table("leads").insert({
        "email": email,
        "consent_given_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": source,
    }).execute()
    return resp.data[0] if resp.data else None


def get_unfollowed_leads():
    """Return all leads where followed_up_at IS NULL."""
    resp = supabase.table("leads").select("*").is_("followed_up_at", "null").execute()
    return resp.data or []


def mark_followed_up(lead_id):
    supabase.table("leads").update({
        "followed_up_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }).eq("id", lead_id).execute()


def email_exists_in_users(email):
    resp = supabase.table("users").select("id").eq("email", email).execute()
    return len(resp.data or []) > 0
