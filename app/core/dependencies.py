from flask import request
from flask import g

from functools import wraps
from app.core.database import db
from app.core.exceptions import AppError
from app.models import User
from app.services.auth_service import AuthService


def get_current_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None

        token = token.strip()
        if token is None:
            return None

        user = AuthService(db.session).get_current_user(token)

        if user is None:
            raise AppError(
                "Could not validate credentials",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        g.current_user = user

        return user

    return wrapper
