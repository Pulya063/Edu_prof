import os

from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppError
from app.models import User
from app.schemas import (
    CollegeScorecardTuitionRefreshRequest,
    TuitionRefreshAcceptedResponse,
    TuitionSnapshotCreateRequest,
    TuitionSnapshotQuery,
    TuitionSnapshotResponse,
    TuitionSnapshotSelection,
)
from app.services.tuition_snapshot_service import TuitionSnapshotService
from app.tasks.tuition_tasks import refresh_college_scorecard_tuition


blueprint = Blueprint("tuition", __name__)


@blueprint.post("/snapshots")
@get_current_user
def create_tuition_snapshot(user: User) -> tuple[Response, int]:
    if not user.is_admin:
        raise AppError("Недостатньо прав для завантаження tuition data", status_code=403)
    payload = TuitionSnapshotCreateRequest.model_validate(request.get_json(silent=True) or {})
    snapshot, created = TuitionSnapshotService(db.session).create(payload)
    response = TuitionSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json")), 201 if created else 200


@blueprint.post("/snapshots/refresh/college-scorecard")
@get_current_user
def queue_college_scorecard_refresh(user: User) -> tuple[Response, int]:
    if not user.is_admin:
        raise AppError("Недостатньо прав для оновлення tuition data", status_code=403)
    if not os.getenv("COLLEGE_SCORECARD_API_KEY"):
        raise AppError("College Scorecard provider не налаштований", status_code=503)

    payload = CollegeScorecardTuitionRefreshRequest.model_validate(
        request.get_json(silent=True) or {}
    )
    try:
        task = refresh_college_scorecard_tuition.delay(payload.scorecard_id)
    except Exception as error:
        raise AppError("Черга оновлення tuition data недоступна", status_code=503) from error

    response = TuitionRefreshAcceptedResponse(job_id=task.id)
    return jsonify(response.model_dump(mode="json")), 202


@blueprint.post("/snapshots/refresh/batch")
@get_current_user
def queue_batch_refresh(user: User) -> tuple[Response, int]:
    if not user.is_admin:
        raise AppError("Недостатньо прав для оновлення tuition data", status_code=403)
        
    payload = request.get_json(silent=True) or {}
    scorecard_ids = payload.get("scorecard_ids")  # optional, None = use config
    
    from app.tasks.tuition_tasks import refresh_tuition_batch
    try:
        task = refresh_tuition_batch.delay(scorecard_ids)
    except Exception as error:
        raise AppError("Черга оновлення tuition data недоступна", status_code=503) from error

    return jsonify({"job_id": task.id, "university_count": len(scorecard_ids) if scorecard_ids else "all"}), 202


@blueprint.get("/snapshots")
@get_current_user
def list_tuition_snapshots(user: User) -> Response:
    query = TuitionSnapshotQuery.model_validate(request.args.to_dict())
    snapshots = TuitionSnapshotService(db.session).list_validated(query)
    response = [
        TuitionSnapshotResponse.model_validate(item).model_dump(mode="json")
        for item in snapshots
    ]
    return jsonify(response)


@blueprint.get("/snapshots/<int:snapshot_id>")
@get_current_user
def get_tuition_snapshot(snapshot_id: int, user: User) -> Response:
    snapshot = TuitionSnapshotService(db.session).get_validated(snapshot_id)
    response = TuitionSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/snapshots/resolve")
@get_current_user
def resolve_tuition_snapshot(user: User) -> Response:
    selection = TuitionSnapshotSelection.model_validate(request.get_json(silent=True) or {})
    snapshot = TuitionSnapshotService(db.session).resolve_validated(selection)
    response = TuitionSnapshotResponse.model_validate(snapshot)
    return jsonify(response.model_dump(mode="json"))
