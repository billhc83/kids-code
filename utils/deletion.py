"""
Account deletion utilities.

Flow:
  1. User or parent calls request_account_deletion() — sets deletion_requested_at timestamp.
  2. After 30 days, run_purge() (called by admin or cron) calls purge_user() for each
     account past its window, cascading across all related tables.

DB prerequisite:
  ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ DEFAULT NULL;
"""

import datetime
from utils.db_client import supabase

_PURGE_AFTER_DAYS = 30


def request_account_deletion(user_id):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    supabase.table("users").update(
        {"deletion_requested_at": now}
    ).eq("id", user_id).execute()


def cancel_deletion_request(user_id):
    supabase.table("users").update(
        {"deletion_requested_at": None}
    ).eq("id", user_id).execute()


def get_pending_deletions():
    resp = (
        supabase.table("users")
        .select("id, username, deletion_requested_at")
        .not_.is_("deletion_requested_at", "null")
        .order("deletion_requested_at")
        .execute()
    )
    return resp.data


def get_accounts_due_for_purge():
    cutoff = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(days=_PURGE_AFTER_DAYS)
    ).isoformat()
    resp = (
        supabase.table("users")
        .select("id, username, deletion_requested_at")
        .not_.is_("deletion_requested_at", "null")
        .lt("deletion_requested_at", cutoff)
        .execute()
    )
    return resp.data


def purge_user(user_id, username):
    """Hard-delete all data for one user. Cascade order avoids FK violations."""
    # Messages inside threads owned by this user
    threads = (
        supabase.table("feedback_threads")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    for t in threads.data:
        supabase.table("feedback_messages").delete().eq("thread_id", t["id"]).execute()

    # Messages sent by this user in other threads
    supabase.table("feedback_messages").delete().eq("sender_id", user_id).execute()

    # Threads
    supabase.table("feedback_threads").delete().eq("user_id", user_id).execute()

    # Challenge submissions
    supabase.table("challenge_submissions").delete().eq("user_id", user_id).execute()

    # Block saves (this table stores user_id in the 'username' column)
    supabase.table("block_saves").delete().eq("username", user_id).execute()

    # Activity logs
    supabase.table("activity_logs").delete().eq("user_id", user_id).execute()

    # Badges
    supabase.table("badges").delete().eq("user_id", user_id).execute()

    # Progression
    supabase.table("progression").delete().eq("user_id", user_id).execute()

    # Parent-student links (both sides)
    supabase.table("parent_student_links").delete().eq("parent_id", user_id).execute()
    supabase.table("parent_student_links").delete().eq("student_id", user_id).execute()

    # User record last
    supabase.table("users").delete().eq("id", user_id).execute()


def run_purge():
    """Purge all accounts past their 30-day window. Returns count purged."""
    accounts = get_accounts_due_for_purge()
    for account in accounts:
        purge_user(account["id"], account["username"])
    return len(accounts)
