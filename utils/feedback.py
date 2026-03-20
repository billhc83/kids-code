import requests
from config import SUPABASE_URL, SUPABASE_KEY
import os

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

CATEGORIES = ["Bug Report", "Suggestion", "Question", "General Feedback"]

def get_threads_for_user(user_id):
    """Get all feedback threads for a user with their messages."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/feedback_threads"
        f"?user_id=eq.{user_id}&order=updated_at.desc",
        headers=HEADERS
    )
    print(f"THREADS STATUS: {resp.status_code}")
    print(f"THREADS RESPONSE: {resp.text}")
    threads = resp.json()
    for thread in threads:
        thread["messages"] = get_messages_for_thread(thread["id"])
    return threads

def get_all_threads():
    """Get all feedback threads for admin view."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/feedback_threads"
        f"?order=updated_at.desc",
        headers=HEADERS
    )
    threads = resp.json()
    for thread in threads:
        thread["messages"] = get_messages_for_thread(thread["id"])
    return threads

def get_messages_for_thread(thread_id):
    """Get all messages for a thread ordered by time."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/feedback_messages"
        f"?thread_id=eq.{thread_id}&order=created_at.asc",
        headers=HEADERS
    )
    return resp.json()

def create_thread(user_id, username, category, subject, message):
    """Create a new feedback thread with the first message."""
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/feedback_threads",
        headers={**HEADERS, "Prefer": "return=representation"},
        json={
            "user_id": user_id,
            "username": username,
            "category": category,
            "subject": subject,
            "status": "open"
        }
    )
    if resp.status_code != 201:
        return None
    thread = resp.json()[0]
    add_message(thread["id"], user_id, username, message, is_admin=False)
    return thread

def add_message(thread_id, sender_id, sender_username, message, is_admin=False):
    """Add a message to a thread and update the thread timestamp."""
    requests.post(
        f"{SUPABASE_URL}/rest/v1/feedback_messages",
        headers=HEADERS,
        json={
            "thread_id": thread_id,
            "sender_id": sender_id,
            "sender_username": sender_username,
            "is_admin": is_admin,
            "message": message
        }
    )
    # Update thread updated_at
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/feedback_threads?id=eq.{thread_id}",
        headers=HEADERS,
        json={"updated_at": "now()"}
    )

def delete_thread(thread_id):
    """Delete a thread and all its messages (cascade handles messages)."""
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/feedback_threads?id=eq.{thread_id}",
        headers=HEADERS
    )

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
