from functools import wraps

from flask import g, request

from app.core.database import db
from app.core.exceptions import AppError
from app.services.auth_service import AuthService


def get_current_user(func):
    """Декоратор: витягує JWT з заголовка, валідує і кладе user у g.current_user."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")

        if scheme.lower() != "bearer" or not token.strip():
            raise AppError(
                "Необхідна авторизація",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = AuthService(db.session).get_current_user(token.strip())

        if user is None:
            raise AppError(
                "Недійсні облікові дані",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Викликаємо оригінальний роут

        kwargs["user"] = user

        return func(*args, **kwargs)

    return wrapper
