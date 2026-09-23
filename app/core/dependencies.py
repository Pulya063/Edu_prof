from functools import wraps

from flask import request

from app.core.database import db
from app.core.exceptions import AppError
from app.services.auth_service import AuthService
from app.core.logging_config import log_call


from flask import g, redirect, url_for

def get_current_user(func):
    """Декоратор: перевіряє g.user, встановлений у before_request."""
    @wraps(func)
    @log_call
    def wrapper(*args, **kwargs):
        if not getattr(g, "user", None):
            # Якщо це HTMX-запит або API-запит, повертаємо 401 для обробки JS
            if request.headers.get("HX-Request") == "true" or request.path.startswith("/api/"):
                raise AppError("Необхідна авторизація", status_code=401)
            # Якщо це звичайний GET-запит сторінки (наприклад, /roadmap), редірект на логін
            return redirect(url_for("pages.login_page"))

        kwargs["user"] = g.user
        return func(*args, **kwargs)

    return wrapper
