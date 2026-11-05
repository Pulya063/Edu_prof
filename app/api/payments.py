from flask import Blueprint, Response, g, jsonify, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import CheckoutRequest
from app.services.payment_service import PaymentService


blueprint = Blueprint("payments", __name__)


@blueprint.get("/plans")
def list_payment_plans() -> Response:
    """Public catalog; reports honestly whether Stripe is configured."""
    response = PaymentService(db.session).list_plans(getattr(g, "user", None))
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/checkout")
@get_current_user
def create_checkout(user: User) -> tuple[Response, int]:
    payload = CheckoutRequest.model_validate(request.get_json(silent=True) or {})
    response = PaymentService(db.session).create_checkout(user, payload)
    return jsonify(response.model_dump(mode="json")), 201


@blueprint.get("/sessions/<string:session_id>")
@get_current_user
def get_payment_status(session_id: str, user: User) -> Response:
    response = PaymentService(db.session).get_status(user, session_id)
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/webhook")
def stripe_webhook() -> tuple[Response, int]:
    outcome = PaymentService(db.session).handle_webhook(
        request.get_data(cache=False),
        request.headers.get("Stripe-Signature"),
    )
    return jsonify({"received": True, "outcome": outcome}), 200
