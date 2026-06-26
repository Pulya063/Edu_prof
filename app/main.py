import logging

from flask import Flask, Response, jsonify
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

    flask_app.register_blueprint(pages.blueprint)
    flask_app.register_blueprint(auth.blueprint, url_prefix="/api/auth")
    flask_app.register_blueprint(roi.blueprint, url_prefix="/api/roi")

    @flask_app.errorhandler(AppError)
    def handle_app_error(error: AppError) -> Response:
        response = jsonify(detail=error.message)
        response.status_code = error.status_code
        for header, value in error.headers.items():
            response.headers[header] = value
        return response

    @flask_app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError) -> tuple[Response, int]:
        return jsonify(detail=error.errors(include_url=False, include_context=False)), 422

    @flask_app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException) -> tuple[Response, int]:
        return jsonify(detail=error.description), error.code or 500

    logger.info("Created Education ROI Calculator Flask app")
    return flask_app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)