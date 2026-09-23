import logging
import os
from flask import Blueprint, Response, jsonify, request, make_response, redirect

from app.core.database import db
from app.schemas import APIResponse, LoginSchema, RegisterSchema, PasswordResetRequestSchema, PasswordResetSchema
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.models import User
from app.services.plan_service import get_plan_details
from app.core.config import auth_cookie_options, refresh_cookie_options

blueprint = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _set_token_cookies(resp: Response, access_token: str, refresh_token: str) -> None:
    """Set both auth cookies on the response."""
    resp.set_cookie("access_token", access_token, **auth_cookie_options())
    resp.set_cookie("refresh_token", refresh_token, **refresh_cookie_options())


def _clear_token_cookies(resp: Response) -> None:
    """Clear both auth cookies (used on logout)."""
    _clear_opts = {k: v for k, v in auth_cookie_options().items() if k in {"path", "domain", "secure", "samesite"}}
    resp.delete_cookie("access_token", **_clear_opts)
    resp.delete_cookie("refresh_token", **_clear_opts)


@blueprint.get("/me")
@get_current_user
def me(user: User) -> Response:
    """Return the logged-in user for the frontend auth shell."""
    plan = get_plan_details(user)
    return jsonify({
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "created_at": user.created_at,
        "plan": plan["name"],
        "plan_limits": {"roi_calculations": plan["limit"], "roadmaps": None},
        "plan_features": plan["features"],
        "usage": {"roi_calculations": plan["used"], "roadmaps": len(user.roadmaps)},
        "calculations_remaining": plan["remaining"],
    })


@blueprint.post("/register")
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
def refresh() -> Response:
    """Rotate the refresh token and issue a new access+refresh pair.

    The old refresh token is immediately revoked (token rotation).
    Returns 401 if the refresh token is missing, invalid, or expired.
    """
    logger.info("Token refresh requested")
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        from app.core.exceptions import AppError
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
    _clear_token_cookies(resp)
    return resp


@blueprint.post("/password-reset-request")
def password_reset_request() -> Response:
    logger.info("Password reset request received")
    data = request.get_json(silent=True) or {}
    payload = PasswordResetRequestSchema.model_validate(data)
    AuthService(db.session).request_password_reset(payload.email)
    # Always return success to prevent email enumeration
    response = APIResponse(message="Якщо email існує в системі, ви отримаєте лист з інструкціями")
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/password-reset")
def password_reset() -> Response:
    logger.info("Processing password reset")
    data = request.get_json(silent=True) or {}
    payload = PasswordResetSchema.model_validate(data)
    AuthService(db.session).reset_password(payload.code, payload.new_password)
    response = APIResponse(message="Пароль успішно змінено")
    return jsonify(response.model_dump(mode="json"))


@blueprint.get("/login/google")
def login_google():
    from app.core.oauth import oauth
    from flask import url_for
    redirect_uri = os.getenv("OAUTH_REDIRECT_URI") or url_for("auth.auth_google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@blueprint.get("/callback/google")
def auth_google_callback():
    from app.core.oauth import oauth
    from app.services.auth_service import AuthService
    from app.models import User
    from sqlalchemy import select
    import secrets as _secrets

    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")

    if not user_info or not user_info.get("email"):
        return Response("Authorization failed", status=400)

    email = user_info["email"]
    service = AuthService(db.session)
    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    if not user:
        random_password = _secrets.token_urlsafe(16) + "A1a"
        from app.schemas import RegisterSchema
        payload = RegisterSchema(email=email, password=random_password)
        user = service.register(payload)

    token_pair = service.create_token_pair(user)

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
    resp = make_response(redirect(f"{frontend_url}/main"))
    _set_token_cookies(resp, token_pair.access_token, token_pair.refresh_token)
    return resp