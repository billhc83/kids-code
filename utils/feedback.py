import requests
from config import SUPABASE_URL, SUPABASE_KEY
import os
from utils.db_client import supabase

CATEGORIES = ["Bug Report", "Suggestion", "Question", "General Feedback"]

def get_threads_for_user(user_id):
    """Get all feedback threads for a user with their messages."""
    resp = supabase.table("feedback_threads").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
    threads = resp.data
    for thread in threads:
        thread["messages"] = get_messages_for_thread(thread["id"])
    return threads

def get_all_threads():
    """Get all feedback threads for admin view."""
    resp = supabase.table("feedback_threads").select("*").order("updated_at", desc=True).execute()
    threads = resp.data
    for thread in threads:
        thread["messages"] = get_messages_for_thread(thread["id"])
    return threads

def get_messages_for_thread(thread_id):
    """Get all messages for a thread ordered by time."""
    resp = supabase.table("feedback_messages").select("*").eq("thread_id", thread_id).order("created_at", desc=False).execute()
    return resp.data

def create_thread(user_id, username, category, subject, message):
    """Create a new feedback thread with the first message."""
    resp = supabase.table("feedback_threads").insert({
        "user_id": user_id,
        "username": username,
        "category": category,
        "subject": subject,
        "status": "open"
    }).execute()
    
    if not resp.data:
        return None
    thread = resp.data[0]
    add_message(thread["id"], user_id, username, message, is_admin=False)
    return thread

def add_message(thread_id, sender_id, sender_username, message, is_admin=False):
    """Add a message to a thread and update the thread timestamp."""
    supabase.table("feedback_messages").insert({
        "thread_id": thread_id,
        "sender_id": sender_id,
        "sender_username": sender_username,
        "is_admin": is_admin,
        "message": message
    }).execute()
    # Update thread updated_at
    # Logic note: Standardizing 'now()' is usually handled by Supabase default or updated_at triggers, 
    # but since it was explicit, we'll use a direct update or let Supabase handle it.
    # supabase-py doesn't have a direct 'now()' string parser like that, we'll let the DB trigger handle it if possible.
    # To mimic 'now()', we can omit it if the table has a default or use datetime.now().
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    supabase.table("feedback_threads").update({"updated_at": now}).eq("id", thread_id).execute()

def delete_thread(thread_id):
    """Delete a thread and all its messages (cascade handles messages)."""
    supabase.table("feedback_threads").delete().eq("id", thread_id).execute()

def has_unread_response(thread):
    """Check if thread has an admin reply the user hasn't seen."""
    messages = thread.get("messages", [])
    return any(m["is_admin"] for m in messages)

def notify_discord_feedback(username, category, subject):
    """Send Discord webhook notification for new feedback."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    payload = {
        "embeds": [
            {
                "title": f"💬 New Feedback: {category}",
                "description": f"**From:** {username}\n**Subject:** {subject}",
                "color": 3066993,
                "footer": {"text": "Check the KidsCode admin panel"}
            }
        ]
    }
    requests.post(webhook_url, json=payload)
