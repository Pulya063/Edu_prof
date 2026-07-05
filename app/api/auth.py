import logging
from flask import Blueprint, Response, jsonify, request, make_response, redirect

from app.core.database import db
from app.schemas import APIResponse, LoginSchema, RegisterSchema, PasswordResetRequestSchema, PasswordResetSchema
from app.services.auth_service import AuthService

blueprint = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@blueprint.post("/register")
def register() -> tuple[Response, int]:
    logger.info("Attempting to register a new user")
    data = request.get_json(silent=True) or request.form.to_dict()
    payload = RegisterSchema.model_validate(data)
    service = AuthService(db.session)
    user = service.register(payload)
    logger.info("User %s registered successfully", user.email)
    response_data = APIResponse(message="Registration successful", data=service.create_access_token(user))
    
    if request.headers.get("HX-Request") == "true":
        resp = make_response("")
        resp.headers["HX-Redirect"] = "/main"
    else:
        resp = make_response(jsonify(response_data.model_dump(mode="json")), 201)
        
    # Set HTTP-only cookie
    resp.set_cookie("access_token", response_data.data.access_token, httponly=True, secure=False, samesite="Lax", path="/")
    return resp


@blueprint.post("/login")
def login() -> Response:
    logger.info("Attempting to log in a user")
    data = request.get_json(silent=True) or request.form.to_dict()
    payload = LoginSchema.model_validate(data)
    token = AuthService(db.session).login(payload)
    logger.info("User %s logged in successfully", payload.email)
    
    if request.headers.get("HX-Request") == "true":
        resp = make_response("")
        resp.headers["HX-Redirect"] = "/main"
    else:
        resp = make_response(jsonify(token.model_dump(mode="json")))
        
    # Set HTTP-only cookie
    resp.set_cookie("access_token", token.access_token, httponly=True, secure=False, samesite="Lax", path="/")
    return resp

@blueprint.post("/logout")
def logout() -> Response:
    logger.info("Logging out user")
    resp = make_response(jsonify({"message": "Logged out successfully"}))
    resp.delete_cookie("access_token", path="/")
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
    AuthService(db.session).reset_password(payload.token, payload.new_password)
    response = APIResponse(message="Пароль успішно змінено")
    return jsonify(response.model_dump(mode="json"))


@blueprint.get("/login/google")
def login_google():
    from app.core.oauth import oauth
    from flask import url_for
    redirect_uri = url_for('auth.auth_google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@blueprint.get("/callback/google")
def auth_google_callback():
    from app.core.oauth import oauth
    from app.services.auth_service import AuthService
    from app.models import User
    from sqlalchemy import select
    import secrets
    
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info or not user_info.get('email'):
        return Response("Authorization failed", status=400)
        
    email = user_info['email']
    service = AuthService(db.session)
    user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    
    if not user:
        random_password = secrets.token_urlsafe(16) + "A1a"
        from app.schemas import RegisterSchema
        payload = RegisterSchema(email=email, password=random_password)
        user = service.register(payload)
        
    access_token = service.create_access_token(user).access_token
    
    # Set the token in cookie and redirect
    resp = make_response(redirect('/main'))
    resp.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="Lax", path="/")
    return resp
