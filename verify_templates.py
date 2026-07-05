import os
from flask import Flask, g
from app.main import create_app

app = create_app()

templates = [
    "base.html",
    "calculator.html",
    "home.html",
    "login.html",
    "main_page.html",
    "profile.html",
    "register.html",
    "roadmap.html"
]

with app.app_context():
    g.user = None
    for tmpl in templates:
        try:
            from flask import render_template
            # Try to render. Some might fail due to missing context vars.
            # We'll see what exceptions are raised.
            render_template(tmpl, calculations=[], user={"email": "test@test.com", "id": 1, "created_at": "2026-07-05"})
            print(f"SUCCESS: {tmpl}")
        except Exception as e:
            print(f"ERROR rendering {tmpl}: {e}")
