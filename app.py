from flask import Flask, render_template, session, request, redirect, url_for, flash, abort
import json
from config import SECRET_KEY, SUPABASE_URL, SUPABASE_KEY, SUPABASE_ANON_KEY
from datetime import timedelta
import os
from dotenv import load_dotenv

from extensions import limiter

# Routes imports
from routes.auth import auth_bp
from routes.lessons import lessons_bp
from routes.admin import admin_bp
from routes.parent import parent_bp
from routes.builder import builder_bp
from routes.main import main_bp

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
app.permanent_session_lifetime = timedelta(days=30)
app.json.sort_keys = False

# Initialize extensions
limiter.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(lessons_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(parent_bp)
app.register_blueprint(builder_bp)
app.register_blueprint(main_bp)

@app.context_processor
def inject_globals():
    unlocked = []
    sidebar_standalone = []
    sidebar_groups = {}
    if "user_id" in session:
        unlocked = get_user_progression(session["user_id"])
        sidebar_standalone, sidebar_groups = get_sidebar_groups(unlocked)
    return {
        "unlocked_lessons": unlocked,
        "sidebar_standalone": sidebar_standalone,
        "sidebar_groups": sidebar_groups,
        "current_endpoint": request.endpoint,
        "hover_zoom": hover_zoom_html,
        "lesson_by_key": LESSON_BY_KEY
    }

if __name__ == "__main__":
    app.run(debug=True, port=5001)