import logging
import os
import traceback
import uuid

import requests

logger = logging.getLogger("kidscode.errors")

_DISCORD_COLOR_CRASH  = 15158332  # red
_DISCORD_COLOR_REPORT = 3447003   # blue


def generate_error_id():
    return uuid.uuid4().hex[:8]


def log_server_error(error_id, exc, path=None, method=None, user_id=None):
    tb_str = traceback.format_exc()
    logger.error(
        "500 [%s] %s %s user=%s\n%s",
        error_id, method, path, user_id, tb_str,
    )
    return tb_str


def _post_discord(payload):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception:
        # Reporting a crash must never itself crash the error handler.
        logger.exception("Failed to post error notification to Discord")


def notify_discord_error(error_id, path, method, username, tb_str):
    tb_excerpt = tb_str[-1500:]
    _post_discord({
        "embeds": [
            {
                "title": f"🔥 Server Error [{error_id}]",
                "description": (
                    f"**Path:** `{method} {path}`\n"
                    f"**User:** {username or 'anonymous'}\n"
                    f"```\n{tb_excerpt}\n```"
                ),
                "color": _DISCORD_COLOR_CRASH,
            }
        ]
    })


def notify_discord_error_report(error_id, who, message):
    _post_discord({
        "embeds": [
            {
                "title": f"📝 User report for [{error_id}]",
                "description": f"**From:** {who}\n**Message:** {message or '(no message provided)'}",
                "color": _DISCORD_COLOR_REPORT,
            }
        ]
    })
