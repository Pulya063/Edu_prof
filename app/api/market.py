from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppError
from app.models import User
from app.schemas import MarketSnapshotCreateRequest, MarketSnapshotQuery, MarketSnapshotResponse
from app.services.market_snapshot_service import MarketSnapshotService


blueprint = Blueprint("market", __name__)


@blueprint.post("/snapshots")
@get_current_user
def create_market_snapshot(user: User) -> tuple[Response, int]:
    if not user.is_admin:
        raise AppError("Недостатньо прав для завантаження market data", status_code=403)
    payload = MarketSnapshotCreateRequest.model_validate(request.get_json(silent=True) or {})
    snapshot, created = MarketSnapshotService(db.session).create(payload)
    response = MarketSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json")), 201 if created else 200


@blueprint.get("/snapshots")
@get_current_user
def list_market_snapshots(user: User) -> Response:
    query = MarketSnapshotQuery.model_validate(request.args.to_dict())
    snapshots = MarketSnapshotService(db.session).list_validated(query)
    response = [
        MarketSnapshotResponse.model_validate(item).model_dump(mode="json")
        for item in snapshots
    ]
    return jsonify(response)


@blueprint.get("/snapshots/<int:snapshot_id>")
@get_current_user
def get_market_snapshot(snapshot_id: int, user: User) -> Response:
    snapshot = MarketSnapshotService(db.session).get_validated(snapshot_id)
    response = MarketSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json"))
