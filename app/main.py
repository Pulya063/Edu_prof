import logging

from flask import Flask, Response, jsonify, request, g
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from app.api import auth, pages, roi
from app.core.database import db
from app.core.exceptions import AppError
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    flask_app = Flask(__name__)
    flask_app.config.update(
        DEBUG=True,
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(flask_app)
    
    # from app.core.oauth import setup_oauth
    from app.api import auth, pages, roi, roadmap

    # flask_app.register_blueprint(auth.blueprint_oauth, url_prefix="/api/oauth")
    flask_app.register_blueprint(auth.blueprint, url_prefix="/api/auth")
    flask_app.register_blueprint(roi.blueprint, url_prefix="/api/roi")
    flask_app.register_blueprint(roadmap.blueprint, url_prefix="/roadmap")
    flask_app.register_blueprint(pages.blueprint)

    @flask_app.before_request
    def load_user_from_cookie():
        from app.services.auth_service import AuthService
        g.user = None
        token = request.cookies.get("access_token")
        if token:
            user = AuthService(db.session).get_current_user(token)
            g.user = user

    @flask_app.errorhandler(AppError)
    def handle_app_error(error: AppError) -> Response | tuple[str, int]:
        logger.warning(f"AppError: {error.message}")
        if request.headers.get("HX-Request") == "true":
            # Повертаємо красиве повідомлення для будь-якої AppError під час HTMX-запиту
            # Завжди статус 200, щоб HTMX міг замінити контент і показати помилку
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
            msg = error.errors()[0].get('msg', 'Невірні дані')
            if 'value is not a valid email address' in msg.lower():
                msg = 'Невірний формат електронної пошти'
            elif 'String should have at least' in msg:
                msg = 'Занадто коротке значення'
            return f'<p class="mt-4 text-sm font-medium text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-3 rounded-lg">Помилка валідації: {msg}</p>', 200
        return jsonify(detail=error.errors(include_url=False, include_context=False)), 422

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[Response, int]:
        logger.warning(f"HTTPException: {error.code} - {error.description}")
        if request.headers.get("HX-Request") == "true":
            from flask import render_template_string
            return render_template_string('<p class="mt-4 text-sm font-medium text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-3 rounded-lg">{{ error }}</p>', error=error.description), 200
        return jsonify(detail=error.description), error.code or 500

    logger.info("Created Education ROI Calculator Flask app")
    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)