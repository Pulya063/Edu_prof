from flask import Blueprint, render_template

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
