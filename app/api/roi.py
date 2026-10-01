import logging
from datetime import datetime, timezone
from flask import Blueprint, Response, g, jsonify, render_template, request
from sqlalchemy import select

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import TrialROIRequest, TrialROIResponse
from app.services.external_api import get_tuition_history, search_universities
from app.services.roi_service import ROIService
from app.services.plan_service import get_plan_details, has_calculation_capacity
from app.core.exceptions import AppError

blueprint = Blueprint("roi", __name__)
logger = logging.getLogger(__name__)


@blueprint.post("/trial")
def calculate_trial_roi() -> Response:
    """Validate trial input and return a validated abbreviated ROI result."""
    data = request.get_json(silent=True) or request.form.to_dict()
    payload = TrialROIRequest.model_validate(data)
    result = ROIService(db.session).analyze_trial(payload)
    response = TrialROIResponse.model_validate(result)
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/analyze")
@get_current_user
def analyze_career(user) -> tuple[Response, int]:
    """Retired legacy writer; existing career analyses remain readable in history."""
    return jsonify(
        {
            "detail": (
                "Legacy career analysis is read-only. Create a versioned scenario and "
                "deterministic projection through /api/simulations."
            ),
            "replacement": {
                "create_scenario": "/api/simulations",
                "create_projection": (
                    "/api/simulations/<scenario_id>/revisions/"
                    "<revision_number>/projections"
                ),
            },
        }
    ), 410


@blueprint.get("/history")
@get_current_user
def roi_history(user) -> Response | str:
    logger.info("Fetching ROI history for user %s", user.id)
    service = ROIService(db.session)

    history = service.get_full_history(user)

    if request.headers.get("X-Count-Only") == "true":
        return str(len(history))

    if request.headers.get("HX-Request") == "true":
        return render_template("partials/history_table.html", calculations=history)

    return jsonify(history)


@blueprint.get("/trash")
@get_current_user
def roi_trash(user: User) -> Response:
    from sqlalchemy import select, desc
    from app.models import ROICalculation

    rows = db.session.execute(
        select(ROICalculation)
        .where(ROICalculation.user_id == user.id, ROICalculation.deleted_at.is_not(None))
        .order_by(desc(ROICalculation.deleted_at))
    ).scalars().all()
    history = ROIService(db.session).serialize_history(rows)
    return jsonify([item.model_dump(mode="json") for item in history])


@blueprint.delete("/<int:calculation_id>")
@get_current_user
def delete_roi(calculation_id: int, user: User) -> Response:
    from app.models import ROICalculation

    calculation = db.session.execute(
        select(ROICalculation).where(ROICalculation.id == calculation_id, ROICalculation.user_id == user.id)
    ).scalar_one_or_none()
    if calculation is None:
        raise AppError("ROI-розрахунок не знайдено", status_code=404)

    db.session.delete(calculation)
    db.session.commit()
    return jsonify({"success": True})


@blueprint.post("/<int:calculation_id>/restore")
@get_current_user
def restore_roi(calculation_id: int, user: User) -> Response:
    from app.models import ROICalculation

    calculation = db.session.execute(
        select(ROICalculation).where(ROICalculation.id == calculation_id, ROICalculation.user_id == user.id)
    ).scalar_one_or_none()
    if calculation is None:
        raise AppError("ROI-розрахунок не знайдено", status_code=404)
    calculation.deleted_at = None
    db.session.commit()
    return jsonify({"success": True})


# ── Пошук університетів ───────────────────────────────────────────────────────

@blueprint.get("/universities/search")
def universities_search() -> Response:
    """
    GET /api/roi/universities/search?q=Harvard
    Повертає список університетів з Hipolabs + College Scorecard (USA).
    """
    query = (request.args.get("q") or "").strip()
    logger.info("Searching for universities with query: %s", query)
    if len(query) < 2:
        return jsonify([])
    results = search_universities(query)
    logger.info("Found %d universities for query: %s", len(results), query)
    return jsonify(results)


# ── Вартість навчання по роках ────────────────────────────────────────────────

@blueprint.get("/universities/tuition")
def universities_tuition() -> Response:
    """
    GET /api/roi/universities/tuition?scorecard_id=123456&country=Ukraine
    Повертає вартість навчання по роках (2018–2023).

    - scorecard_id — ID з College Scorecard (для університетів США)
    - country      — назва країни (для TuitionPrice table)
    """
    raw_id  = request.args.get("scorecard_id")
    country = (request.args.get("country") or "").strip()
    logger.info("Fetching tuition history for scorecard_id=%s, country=%s", raw_id, country)

    scorecard_id = int(raw_id) if raw_id and raw_id.isdigit() else None

    if not scorecard_id and not country:
        logger.warning("scorecard_id or country is required")
        return jsonify({"error": "Потрібен scorecard_id або country"}), 400

    history = get_tuition_history(scorecard_id, country, db.session)
    logger.info("Found %d tuition history records", len(history))
    return jsonify(history)
