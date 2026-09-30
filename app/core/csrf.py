"""CSRF protection for the cookie-authenticated API."""

from __future__ import annotations

import hmac
import secrets

from flask import Response, request

from app.core.config import auth_cookie_options, get_refresh_token_ttl
from app.core.exceptions import AppError

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
_EXEMPT_ENDPOINTS = {
    "auth.register",
    "auth.login",
    "auth.password_reset_request",
    "auth.password_reset",
    "auth.login_google",
    "auth.auth_google_callback",
}


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_cookie_options() -> dict[str, object]:
    options = auth_cookie_options().copy()
    options["httponly"] = False
    options["max_age"] = get_refresh_token_ttl()
    return options


def set_csrf_cookie(response: Response, token: str | None = None) -> str:
    value = token or generate_csrf_token()
    response.set_cookie(CSRF_COOKIE_NAME, value, **csrf_cookie_options())
    return value


def clear_csrf_cookie(response: Response) -> None:
    options = csrf_cookie_options()
    delete_options = {key: value for key, value in options.items() if key in {"path", "domain", "secure", "samesite"}}
    response.delete_cookie(CSRF_COOKIE_NAME, **delete_options)


def validate_csrf_request() -> None:
    if request.method in _SAFE_METHODS or request.endpoint in _EXEMPT_ENDPOINTS:
        return
    if not (request.cookies.get("access_token") or request.cookies.get("refresh_token")):
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_token = request.headers.get(CSRF_HEADER_NAME, "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise AppError("CSRF token відсутній або недійсний", status_code=403)
