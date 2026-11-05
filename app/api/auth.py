import logging
import os
from flask import Blueprint, Response, current_app, g, jsonify, request, make_response, redirect

from app.core.database import db
from app.schemas import APIResponse, AuthMeResponse, AuthProvidersResponse, LoginSchema, RegisterSchema, PasswordResetRequestSchema, PasswordResetSchema
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.models import User
from app.services.plan_service import get_plan_details
from app.core.config import auth_cookie_options, refresh_cookie_options
from app.core.csrf import clear_csrf_cookie, set_csrf_cookie
from app.core.exceptions import AppError
from app.core.rate_limit import normalized_email_rate_key, rate_limit

blueprint = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _set_token_cookies(resp: Response, access_token: str, refresh_token: str) -> None:
    """Set both auth cookies on the response."""
    resp.set_cookie("access_token", access_token, **auth_cookie_options())
    resp.set_cookie("refresh_token", refresh_token, **refresh_cookie_options())
    set_csrf_cookie(resp)


def _clear_token_cookies(resp: Response) -> None:
    """Clear both auth cookies (used on logout)."""
    _clear_opts = {k: v for k, v in auth_cookie_options().items() if k in {"path", "domain", "secure", "samesite"}}
    resp.delete_cookie("access_token", **_clear_opts)
    resp.delete_cookie("refresh_token", **_clear_opts)
    clear_csrf_cookie(resp)


@blueprint.get("/me")
@get_current_user
def me(user: User) -> Response:
    """Return the logged-in user for the frontend auth shell."""
    plan = get_plan_details(user)
    response = AuthMeResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        plan=plan["name"],
        plan_limits={"roi_calculations": plan["limit"], "roadmaps": None},
        plan_features=plan["features"],
        usage={"roi_calculations": plan["used"], "roadmaps": len(user.roadmaps)},
        calculations_remaining=plan["remaining"],
        is_admin=user.is_admin,
    )
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/register")
@rate_limit(5, 60 * 60, "auth-register")
def register() -> tuple[Response, int]:
    logger.info("Attempting to register a new user")
    data = request.get_json(silent=True) or request.form.to_dict()
    payload = RegisterSchema.model_validate(data)
    service = AuthService(db.session)
    user = service.register(payload)
    logger.info("User %s registered successfully", user.email)
    token_pair = service.create_token_pair(user)

    if request.headers.get("HX-Request") == "true":
        resp = make_response("")
        resp.headers["HX-Redirect"] = "/main"
    else:
        response_data = APIResponse(
            message="Registration successful",
            data={"access_token": token_pair.access_token, "token_type": token_pair.token_type},
        )
        resp = make_response(jsonify(response_data.model_dump(mode="json")), 201)

    _set_token_cookies(resp, token_pair.access_token, token_pair.refresh_token)
    return resp


@blueprint.post("/login")
@rate_limit(10, 60, "auth-login")
def login() -> Response:
    logger.info("Attempting to log in a user")
    data = request.get_json(silent=True) or request.form.to_dict()
    payload = LoginSchema.model_validate(data)
    token_pair = AuthService(db.session).login(payload)
    logger.info("User %s logged in successfully", payload.email)

    if request.headers.get("HX-Request") == "true":
        resp = make_response("")
        resp.headers["HX-Redirect"] = "/main"
    else:
        resp = make_response(jsonify({
            "access_token": token_pair.access_token,
            "token_type": token_pair.token_type,
        }))

    _set_token_cookies(resp, token_pair.access_token, token_pair.refresh_token)
    return resp


@blueprint.post("/refresh")
@rate_limit(30, 60, "auth-refresh")
def refresh() -> Response:
    """Rotate the refresh token and issue a new access+refresh pair.

    The old refresh token is immediately revoked (token rotation).
    Returns 401 if the refresh token is missing, invalid, or expired.
    """
    logger.info("Token refresh requested")
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise AppError("Refresh token відсутній", status_code=401)

    token_pair = AuthService(db.session).refresh_tokens(refresh_token)
    logger.info("Token pair rotated successfully")

    resp = make_response(jsonify({
        "access_token": token_pair.access_token,
        "token_type": token_pair.token_type,
    }))
    _set_token_cookies(resp, token_pair.access_token, token_pair.refresh_token)
    return resp


@blueprint.post("/logout")
def logout() -> Response:
    logger.info("Logging out user")
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        AuthService(db.session).revoke_refresh_token(refresh_token)

    resp = make_response(jsonify({"message": "Logged out successfully"}))
    g.clear_auth_cookies = True
    _clear_token_cookies(resp)
    return resp


@blueprint.post("/password-reset-request")
@rate_limit(5, 60 * 60, "auth-reset-request-ip")
@rate_limit(3, 60 * 60, "auth-reset-request-email", key_func=normalized_email_rate_key)
def password_reset_request() -> Response:
    logger.info("Password reset request received")
    data = request.get_json(silent=True) or {}
    payload = PasswordResetRequestSchema.model_validate(data)
    AuthService(db.session).request_password_reset(payload.email)
    # Always return success to prevent email enumeration
    response = APIResponse(message="Якщо email існує в системі, ви отримаєте лист з інструкціями")
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/password-reset")
@rate_limit(10, 60 * 60, "auth-reset")
def password_reset() -> Response:
    logger.info("Processing password reset")
    data = request.get_json(silent=True) or {}
    payload = PasswordResetSchema.model_validate(data)
    AuthService(db.session).reset_password(payload.code, payload.new_password)
    response = APIResponse(message="Пароль успішно змінено")
    return jsonify(response.model_dump(mode="json"))


_OAUTH_NEXT_SESSION_KEY = "oauth_next"


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3221").rstrip("/")


def _safe_next_path(value: str | None) -> str | None:
    """Only same-site workspace/payment paths may be used as a post-login destination."""
    if not value or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return None
    if value.startswith("/workspace/") or value == "/payment" or value.startswith(("/payment?", "/payment/")):
        return value
    return None


def google_redirect_uri() -> str:
    # The callback goes through the frontend origin (Next.js proxies /api/*), so the auth
    # cookies and the OAuth state cookie live on the same site the user is browsing.
    return os.getenv("OAUTH_REDIRECT_URI", "").strip() or f"{_frontend_url()}/api/auth/callback/google"


def _oauth_failure(reason: str) -> Response:
    return redirect(f"{_frontend_url()}/login?oauth_error={reason}")


@blueprint.get("/providers")
def auth_providers() -> Response:
    """Tell the login/register pages which external sign-in options are configured."""
    response = AuthProvidersResponse(
        google={"configured": bool(current_app.config.get("GOOGLE_OAUTH_CONFIGURED", False))}
    )
    return jsonify(response.model_dump(mode="json"))


@blueprint.get("/login/google")
@rate_limit(20, 60 * 60, "auth-google")
def login_google():
    if not current_app.config.get("GOOGLE_OAUTH_CONFIGURED", False):
        raise AppError("Google OAuth не налаштовано", status_code=503)
    from flask import session
    from app.core.oauth import oauth

    next_path = _safe_next_path(request.args.get("next"))
    if next_path:
        session[_OAUTH_NEXT_SESSION_KEY] = next_path
    else:
        session.pop(_OAUTH_NEXT_SESSION_KEY, None)
    return oauth.google.authorize_redirect(google_redirect_uri())


@blueprint.get("/callback/google")
def auth_google_callback():
    if not current_app.config.get("GOOGLE_OAUTH_CONFIGURED", False):
        raise AppError("Google OAuth не налаштовано", status_code=503)
    from authlib.integrations.base_client.errors import OAuthError
    from flask import session
    from redis.exceptions import RedisError
    from sqlalchemy import select
    import secrets as _secrets

    from app.core.oauth import oauth
    from app.schemas import RegisterSchema

    if request.args.get("error"):
        # The user pressed "Cancel" on Google's consent screen, or Google refused the request.
        logger.info("Google OAuth returned error=%s", request.args.get("error"))
        return _oauth_failure("cancelled" if request.args.get("error") == "access_denied" else "google_failed")

    try:
        token = oauth.google.authorize_access_token()
    except OAuthError as error:
        # Includes state mismatch (CSRF) and invalid/expired authorization codes.
        logger.warning("Google OAuth token exchange failed: %s", error.error)
        return _oauth_failure("google_failed")
    except Exception:
        logger.exception("Google OAuth token exchange crashed")
        return _oauth_failure("google_failed")

    user_info = token.get("userinfo") or {}
    email = str(user_info.get("email") or "").strip().lower()
    if not email:
        return _oauth_failure("google_failed")
    if user_info.get("email_verified") is not True:
        # Never attach an unverified Google address to an existing Fence account.
        logger.warning("Rejected Google sign-in with unverified email")
        return _oauth_failure("email_unverified")

    service = AuthService(db.session)
    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        user = service.register(RegisterSchema(email=email, password=_secrets.token_urlsafe(16) + "A1a"))
        logger.info("Created account via Google user_id=%s", user.id)
    elif not user.is_active:
        return _oauth_failure("account_disabled")

    try:
        token_pair = service.create_token_pair(user)
    except RedisError as error:
        logger.warning("Google sign-in token storage unavailable: %s", error)
        return _oauth_failure("unavailable")

    next_path = _safe_next_path(session.pop(_OAUTH_NEXT_SESSION_KEY, None))
    success_url = (
        f"{_frontend_url()}{next_path}"
        if next_path
        else os.getenv("OAUTH_SUCCESS_URL", "").strip() or f"{_frontend_url()}/workspace/overview"
    )
    resp = make_response(redirect(success_url))
    _set_token_cookies(resp, token_pair.access_token, token_pair.refresh_token)
    return resp
