from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import (
    RoadmapPreviewRequest,
    RoadmapTaskUpdate,
    WorkspaceCourseResponse,
    WorkspacePreferences,
    WorkspaceProfileUpdate,
    WorkspaceStateResponse,
    WorkspaceUniversityResponse,
)
from app.services.workspace_service import WorkspaceService, preview_roadmap

blueprint = Blueprint("workspace", __name__)


@blueprint.get("")
@get_current_user
def get_workspace(user: User) -> Response:
    response = WorkspaceStateResponse.model_validate(WorkspaceService(db.session).state_for_user(user))
    return jsonify(response.model_dump(mode="json"))


@blueprint.patch("/profile")
@get_current_user
def update_profile(user: User) -> Response:
    payload = WorkspaceProfileUpdate.model_validate(request.get_json(silent=True) or {})
    response = WorkspaceStateResponse.model_validate(WorkspaceService(db.session).update_profile(user, payload.username, payload.profile))
    return jsonify(response.model_dump(mode="json"))


@blueprint.patch("/preferences")
@get_current_user
def update_preferences(user: User) -> Response:
    payload = WorkspacePreferences.model_validate(request.get_json(silent=True) or {})
    response = WorkspaceStateResponse.model_validate(WorkspaceService(db.session).update_preferences(user, payload))
    return jsonify(response.model_dump(mode="json"))


@blueprint.get("/universities")
@get_current_user
def list_universities(user: User) -> Response:
    results = WorkspaceService(db.session).universities((request.args.get("country") or "").strip(), (request.args.get("faculty") or "").strip(), (request.args.get("q") or "").strip())
    response = [WorkspaceUniversityResponse.model_validate(item).model_dump(mode="json") for item in results]
    return jsonify(response)


@blueprint.get("/courses")
@get_current_user
def list_courses(user: User) -> Response:
    results = WorkspaceService(db.session).courses(user, request.args.get("q") or "", request.args.get("level") or "", request.args.get("language") or "", request.args.get("format") or "")
    response = [WorkspaceCourseResponse.model_validate(item).model_dump(mode="json") for item in results]
    return jsonify(response)


@blueprint.post("/courses/<string:course_id>/save")
@get_current_user
def save_course(course_id: str, user: User) -> Response:
    response = WorkspaceCourseResponse.model_validate(WorkspaceService(db.session).set_course_saved(user, course_id, True))
    return jsonify(response.model_dump(mode="json"))


@blueprint.delete("/courses/<string:course_id>/save")
@get_current_user
def unsave_course(course_id: str, user: User) -> Response:
    response = WorkspaceCourseResponse.model_validate(WorkspaceService(db.session).set_course_saved(user, course_id, False))
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/roadmap/preview")
@get_current_user
def roadmap_preview(user: User) -> Response:
    payload = RoadmapPreviewRequest.model_validate(request.get_json(silent=True) or {})
    return jsonify(preview_roadmap(payload))


@blueprint.patch("/roadmaps/<int:roadmap_id>/tasks/<string:task_id>")
@get_current_user
def update_roadmap_task(roadmap_id: int, task_id: str, user: User) -> Response:
    payload = RoadmapTaskUpdate.model_validate(request.get_json(silent=True) or {})
    return jsonify(WorkspaceService(db.session).update_roadmap_task(user, roadmap_id, task_id, payload.completed))
