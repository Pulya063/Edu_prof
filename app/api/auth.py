from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.schemas import APIResponse, LoginSchema, RegisterSchema
from app.services.auth_service import AuthService

blueprint = Blueprint("auth", __name__)


@blueprint.post("/register")
def register() -> tuple[Response, int]:
    data = request.get_json(silent=True) or {}
    print(f"[DEBUG REGISTER] Incoming payload: {data}", flush=True)
    payload = RegisterSchema.model_validate(data)
    service = AuthService(db.session)
    user = service.register(payload)
    response = APIResponse(message="Registration successful", data=service.create_access_token(user))
    return jsonify(response.model_dump(mode="json")), 201


@blueprint.post("/login")
def login() -> Response:
    data = request.get_json(silent=True) or {}
    print(f"[DEBUG LOGIN] Incoming payload: {data}", flush=True)
    payload = LoginSchema.model_validate(data)
    token = AuthService(db.session).login(payload)
    return jsonify(token.model_dump(mode="json"))
