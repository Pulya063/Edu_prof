import os


def is_production() -> bool:
    return os.getenv("APP_ENV", "development").lower() == "production"


def auth_cookie_options() -> dict[str, object]:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3221")
    secure = is_production() or frontend_url.startswith("https://")
    return {
        "httponly": True,
        "secure": secure,
        "samesite": os.getenv("AUTH_COOKIE_SAMESITE", "Lax"),
        "path": "/",
    }


def get_refresh_token_ttl() -> int:
    """Return refresh token lifetime in seconds (default: 30 days)."""
    days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    return days * 24 * 60 * 60


def refresh_cookie_options() -> dict[str, object]:
    """Cookie options for the long-lived refresh token cookie."""
    opts = auth_cookie_options()
    opts["max_age"] = get_refresh_token_ttl()
    return opts
