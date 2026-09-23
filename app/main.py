import logging
import os

from flask import Flask, Response, jsonify, request, g
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.api import auth, roi
from app.core.database import db
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging, register_request_logging
from dotenv import load_dotenv
from app.core.config import is_production

load_dotenv()

configure_logging()
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    logger.info("Creating Flask application")
    flask_app = Flask(__name__)
    flask_app.config.update(
        DEBUG=not is_production(),
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(flask_app)
    register_request_logging(flask_app)

    # Initialise Redis (logs a warning, does not crash, if Redis is down)
    from app.core.redis_client import init_redis
    with flask_app.app_context():
        init_redis()

    @flask_app.get("/health")
    def health_check() -> tuple[dict[str, str], int]:
        return {"status": "ok"}, 200

    from app.api import auth, mail, roi, roadmap
    from app.api import resource_audit

    flask_app.register_blueprint(auth.blueprint, url_prefix="/api/auth")
    flask_app.register_blueprint(roi.blueprint, url_prefix="/api/roi")
    flask_app.register_blueprint(mail.blueprint, url_prefix="/api/mail")
    flask_app.register_blueprint(roadmap.blueprint, url_prefix="/roadmap")
    # JSON API namespace used by the Next.js application.
    flask_app.register_blueprint(roadmap.blueprint, url_prefix="/api/roadmap", name="roadmap_api")
    flask_app.register_blueprint(resource_audit.blueprint)

    @flask_app.before_request
    def load_user_from_cookie():
        from app.services.auth_service import AuthService
        from app.core.config import auth_cookie_options, refresh_cookie_options

        g.user = None
        g.new_tokens = None  # filled when silent refresh occurs

        access_token = request.cookies.get("access_token")
        if access_token:
            user = AuthService(db.session).get_current_user(access_token)
            if user:
                g.user = user
                logger.info("Authenticated request user_id=%s", user.id)
                return

        # --- Silent refresh: access token missing/expired, try refresh token ---
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            try:
                token_pair = AuthService(db.session).refresh_tokens(refresh_token)
                # Re-resolve user from fresh access token
                user = AuthService(db.session).get_current_user(token_pair.access_token)
                if user:
                    g.user = user
                    g.new_tokens = token_pair
                    logger.info(
                        "Silent refresh succeeded for user_id=%s", user.id
                    )
            except AppError:
                # Refresh token invalid — user stays unauthenticated
                logger.debug("Silent refresh failed — refresh token invalid/expired")

    @flask_app.after_request
    def apply_new_tokens(response: Response) -> Response:
        """If a silent refresh happened, write the new cookies onto the response."""
        token_pair = getattr(g, "new_tokens", None)
        if token_pair is not None:
            from app.core.config import auth_cookie_options, refresh_cookie_options
            response.set_cookie("access_token", token_pair.access_token, **auth_cookie_options())
            response.set_cookie("refresh_token", token_pair.refresh_token, **refresh_cookie_options())
        return response

    @flask_app.errorhandler(AppError)
    def handle_app_error(error: AppError) -> Response | tuple[str, int]:
        logger.warning(f"AppError: {error.message}")
        if request.headers.get("HX-Request") == "true":
            msg = error.message
            if error.status_code == 401:
                msg = "Необхідна авторизація. Будь ласка, увійдіть в систему."
            return f'<p class="mt-4 text-sm font-medium text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-3 rounded-lg">{msg}</p>', 200

        response = jsonify(detail=error.message)
        response.status_code = error.status_code
        for header, value in error.headers.items():
            response.headers[header] = value
        return response

    @flask_app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Response | str, int]:
        logger.warning(f"Validation error: {error.errors()}")
        if request.headers.get("HX-Request") == "true":
            msg = error.errors()[0].get("msg", "Невірні дані")
            if "value is not a valid email address" in msg.lower():
                msg = "Невірний формат електронної пошти"
            elif "String should have at least" in msg:
                msg = "Занадто коротке значення"
            return f'<p class="mt-4 text-sm font-medium text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-3 rounded-lg">Помилка валідації: {msg}</p>', 200
        return jsonify(detail=error.errors(include_url=False, include_context=False)), 422

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[Response, int]:
        logger.warning(f"HTTPException: {error.code} - {error.description}")
        if request.headers.get("HX-Request") == "true":
            from flask import render_template_string
            return render_template_string(
                '<p class="mt-4 text-sm font-medium text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-3 rounded-lg">{{ error }}</p>',
                error=error.description,
            ), 200
        return jsonify(detail=error.description), error.code or 500

    logger.info("Created Education ROI Calculator Flask app")
    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8122, debug=app.debug)
