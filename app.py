from flask import Flask, render_template, session, request, redirect, url_for, flash, abort
import json
from config import SECRET_KEY, SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY
from datetime import timedelta
import os
from dotenv import load_dotenv

from extensions import limiter, csrf
from utils.error_reporting import generate_error_id, log_server_error, notify_discord_error

# Routes imports
from routes.auth import auth_bp
from routes.lessons import lessons_bp
from routes.admin import admin_bp
from routes.parent import parent_bp
from routes.teacher import teacher_bp
from routes.onboarding import onboarding_bp
from routes.builder import builder_bp
from routes.main import main_bp
from routes.help import help_bp
from routes.dev import dev_bp
from routes.account import account_bp
from routes.try_it import try_it_bp
from routes.billing import billing_bp

from utils.progression import get_user_progression
from utils.lessons import get_sidebar_groups, LESSON_BY_KEY
from utils.hover_zoom import hover_zoom_html

load_dotenv()

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is missing")
if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY environment variable is missing")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=8)
app.json.sort_keys = False

# Initialize extensions
limiter.init_app(app)
csrf.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(lessons_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(parent_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(onboarding_bp)
app.register_blueprint(builder_bp)
app.register_blueprint(main_bp)
app.register_blueprint(help_bp)
app.register_blueprint(dev_bp)
app.register_blueprint(account_bp)
app.register_blueprint(try_it_bp)
app.register_blueprint(billing_bp)

_TOS_EXEMPT_PREFIXES = ("/static/", "/welcome/agree", "/logout",
                        "/privacy", "/terms", "/favicon")

@app.before_request
def require_tos_agreement():
    if not session.get("needs_tos_agreement"):
        return
    path = request.path
    for prefix in _TOS_EXEMPT_PREFIXES:
        if path.startswith(prefix):
            return
    if request.endpoint in ("auth.logout", "onboarding.agree_tos", "static"):
        return
    return redirect(url_for("onboarding.agree_tos"))

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "media-src 'self' https://github.com https://*.githubusercontent.com; "
        "connect-src 'self' http://127.0.0.1:52010 ws://127.0.0.1:52011 https://cdnjs.cloudflare.com; "
        "worker-src blob:; "
        "frame-ancestors 'self';"
    )
    return response

@app.context_processor
def inject_globals():
    unlocked = []
    sidebar_standalone = []
    sidebar_groups = {}
    if "user_id" in session:
        try:
            unlocked = get_user_progression(session["user_id"])
            sidebar_standalone, sidebar_groups = get_sidebar_groups(unlocked)
        except Exception:
            # Degrade to empty sidebar/progression rather than let a DB hiccup
            # take down every page render on the site (including the error page).
            app.logger.exception("inject_globals: failed to load progression/sidebar")
    return {
        "unlocked_lessons": unlocked,
        "sidebar_standalone": sidebar_standalone,
        "sidebar_groups": sidebar_groups,
        "current_endpoint": request.endpoint,
        "hover_zoom": hover_zoom_html,
        "lesson_by_key": LESSON_BY_KEY
    }

_FALLBACK_ERROR_HTML = """<!DOCTYPE html><html><head><title>KidsCode</title></head>
<body style="font-family:sans-serif;text-align:center;padding:60px 20px;">
<h1>{heading}</h1><p>{message}</p><p><a href="/">Back to KidsCode</a></p>
</body></html>"""

@app.errorhandler(500)
def handle_server_error(exc):
    error_id = generate_error_id()
    tb_str = log_server_error(
        error_id, exc, path=request.path, method=request.method,
        user_id=session.get("user_id"),
    )
    notify_discord_error(
        error_id, request.path, request.method,
        session.get("username"), tb_str,
    )
    try:
        return render_template("error.html", mode="crash", error_id=error_id), 500
    except Exception:
        app.logger.exception("Failed to render error.html for a 500 — using inline fallback")
        return _FALLBACK_ERROR_HTML.format(
            heading="Something broke on our end 🛠️",
            message=f"Sorry about that! Error ID: {error_id}",
        ), 500

@app.errorhandler(404)
def handle_not_found(exc):
    try:
        return render_template("error.html", mode="not_found"), 404
    except Exception:
        app.logger.exception("Failed to render error.html for a 404 — using inline fallback")
        return _FALLBACK_ERROR_HTML.format(
            heading="Page not found",
            message="That page doesn't exist.",
        ), 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)