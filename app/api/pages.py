from flask import Blueprint, render_template
from app.core.dependencies import get_current_user

blueprint = Blueprint("pages", __name__)


@blueprint.get("/")
def home() -> str:
    return render_template("home.html")


@blueprint.get("/login")
def login_page() -> str:
    return render_template("login.html")


@blueprint.get("/register")
def register_page() -> str:
    return render_template("register.html")


@blueprint.get("/calculator")
def calculator_page() -> str:
    return render_template("calculator.html")


@blueprint.get("/main")
@get_current_user
def main_page(user) -> str:
    return render_template("main_page.html")


@blueprint.get("/profile")
@get_current_user
def profile_page(user) -> str:
    return render_template("profile.html")
