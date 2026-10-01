import logging
from flask import Blueprint, Response, jsonify, render_template, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import UserRoadmap, User
from app.schemas import RoadmapGenerateRequest, RoadmapPreviewRequest, UserRoadmapResponse
from app.services.dreamwork_integration import DreamworkClient, DreamworkClientError
from app.services.workspace_service import build_local_roadmap
from sqlalchemy import desc, select

blueprint = Blueprint("roadmap", __name__)
logger = logging.getLogger(__name__)


@blueprint.get("/")
@get_current_user
def get_roadmap_page(user: User) -> Response | str:
    logger.info("Fetching roadmap page for user %s", user.id)
    result = db.session.execute(
        select(UserRoadmap)
        .where(UserRoadmap.user_id == user.id)
        .order_by(desc(UserRoadmap.created_at))
    )
    latest_roadmap = result.scalars().first()
    
    if request.headers.get("Accept") == "application/json":
        if latest_roadmap:
            response_model = UserRoadmapResponse.model_validate(latest_roadmap)
            return jsonify({"success": True, "data": response_model.model_dump(mode="json")})
        return jsonify({"success": True, "data": None})
        
    return render_template("roadmap.html", roadmap=latest_roadmap)


@blueprint.post("/generate")
@get_current_user
def generate_roadmap(user: User) -> Response | str:
    logger.info("Generating roadmap for user %s", user.id)
    try:
        payload = RoadmapGenerateRequest.model_validate(
            request.get_json(silent=True) or request.form.to_dict()
        )
    except Exception as e:
        logger.error(f"Invalid request payload: {e}")
        return jsonify({"success": False, "message": "Неправильні вхідні дані"}), 400

    client = DreamworkClient()
    try:
        plan_data = client.get_roadmap(
            target_job=payload.target_job,
            hours_per_week=payload.hours_per_week,
            current_income=payload.current_income,
            skills=payload.skills
        )
        
        dreamwork_plan_id = plan_data.get("id")
        fallback = build_local_roadmap(
            RoadmapPreviewRequest(
                target_job=payload.target_job,
                current_level="Beginner",
                hours_per_week=payload.hours_per_week,
                skills=payload.skills,
            ),
            source="dreamwork",
        )
        plan_data = {**plan_data, "source": "dreamwork", "normalized": fallback["normalized"]}
        
        # Збереження в нашу БД
        user_roadmap = UserRoadmap(
            user_id=user.id,
            target_job=payload.target_job,
            dreamwork_plan_id=dreamwork_plan_id,
            roadmap_data=plan_data
        )
        db.session.add(user_roadmap)
        db.session.commit()
        
        if request.headers.get("HX-Request") == "true":
            return render_template("partials/roadmap_timeline.html", roadmap=user_roadmap)
            
        response_model = UserRoadmapResponse.model_validate(user_roadmap)
        return jsonify({"success": True, "data": response_model.model_dump(mode="json")})

    except DreamworkClientError as e:
        logger.warning("Dreamwork unavailable; creating local roadmap for user %s: %s", user.id, e)
        local_plan = build_local_roadmap(
            RoadmapPreviewRequest(
                target_job=payload.target_job,
                current_level="Beginner",
                hours_per_week=payload.hours_per_week,
                skills=payload.skills,
            )
        )
        user_roadmap = UserRoadmap(
            user_id=user.id,
            target_job=payload.target_job,
            dreamwork_plan_id=None,
            roadmap_data=local_plan,
        )
        db.session.add(user_roadmap)
        db.session.commit()
        response_model = UserRoadmapResponse.model_validate(user_roadmap)
        return jsonify({
            "success": True,
            "data": response_model.model_dump(mode="json"),
            "warning": "DreamWork недоступний — створено локальний план Fence.",
        }), 201
    except Exception as e:
        logger.error(f"Unexpected error during roadmap generation: {e}")
        return jsonify({"success": False, "message": "Внутрішня помилка сервера"}), 500
