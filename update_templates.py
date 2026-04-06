import os
import re

replacements = {
    r"url_for\('login'\)": "url_for('auth.login')",
    r'url_for\("login"\)': 'url_for("auth.login")',
    
    r"url_for\('logout'\)": "url_for('auth.logout')",
    r'url_for\("logout"\)': 'url_for("auth.logout")',
    
    r"url_for\('register'\)": "url_for('auth.register')",
    r'url_for\("register"\)': 'url_for("auth.register")',
    
    r"url_for\('check_email'\)": "url_for('auth.check_email')",
    r'url_for\("check_email"\)': 'url_for("auth.check_email")',
    
    r"url_for\('forgot_password'\)": "url_for('auth.forgot_password')",
    r'url_for\("forgot_password"\)': 'url_for("auth.forgot_password")',
    
    r"url_for\('dashboard'\)": "url_for('main.dashboard')",
    r'url_for\("dashboard"\)': 'url_for("main.dashboard")',
    
    r"url_for\('parent_dashboard'\)": "url_for('parent.parent_dashboard')",
    r'url_for\("parent_dashboard"\)': 'url_for("parent.parent_dashboard")',
    
    r"url_for\('admin_dashboard'\)": "url_for('admin.admin_dashboard')",
    r'url_for\("admin_dashboard"\)': 'url_for("admin.admin_dashboard")',
    
    r"url_for\('feedback'\)": "url_for('main.feedback')",
    r'url_for\("feedback"\)': 'url_for("main.feedback")',
    
    r"url_for\('index'\)": "url_for('main.index')",
    r'url_for\("index"\)': 'url_for("main.index")',
    
    r"url_for\('lesson'": "url_for('lessons.lesson'",
    r'url_for\("lesson"': 'url_for("lessons.lesson"',
    
    r"url_for\('challenge'": "url_for('lessons.challenge'",
    r'url_for\("challenge"': 'url_for("lessons.challenge"',

    r"url_for\('preset_builder'\)": "url_for('admin.preset_builder')",
    r'url_for\("preset_builder"\)': 'url_for("admin.preset_builder")',
    
    r"url_for\('step_builder'\)": "url_for('admin.step_builder')",
    r'url_for\("step_builder"\)': 'url_for("admin.step_builder")',

    r"url_for\('complete_lesson_route'\)": "url_for('lessons.complete_lesson_route')",
    r'url_for\("complete_lesson_route"\)': 'url_for("lessons.complete_lesson_route")',
}

templates_dir = "templates"

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = re.sub(old, new, new_content)
                
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path}")
