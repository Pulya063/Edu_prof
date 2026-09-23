import logging
from datetime import datetime, timezone
from flask import Blueprint, Response, g, jsonify, render_template, request
from sqlalchemy import select

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import CareerAnalysisRequest, ROICalculationRequest
from app.services.external_api import get_tuition_history, search_universities
from app.services.roi_service import ROIService
from app.services.plan_service import get_plan_details, has_calculation_capacity
from app.core.exceptions import AppError

blueprint = Blueprint("roi", __name__)
logger = logging.getLogger(__name__)


# ── ROI калькулятор ───────────────────────────────────────────────────────────

@blueprint.post("/calculate")
@get_current_user
def calculate_roi(user: User) -> Response | str:
    logger.info("Calculating ROI for user %s", user.id)
    if not has_calculation_capacity(user):
        plan = get_plan_details(user)
        return jsonify({
            "detail": "Досягнуто ліміт ROI-розрахунків для вашого плану.",
            "code": "CALCULATION_LIMIT_REACHED",
            "plan": plan["name"],
            "used": plan["used"],
            "limit": plan["limit"],
        }), 403
    payload = ROICalculationRequest.model_validate(
        request.get_json(silent=True) or request.form.to_dict()
    )
    result = ROIService(db.session).calculate_roi(payload, user)
    if request.headers.get("HX-Request") == "true":
        logger.info("Returning ROI results as HTML partial")
        return render_template("partials/roi_results.html", result=result)
    logger.info("Returning ROI results as JSON")
    return jsonify(result.model_dump(mode="json"))


@blueprint.post("/trial")
def calculate_trial_roi() -> Response:
    """Return and persist the full anonymous career analysis.

    The legacy three-field ROI payload remains accepted for existing clients;
    the full analysis contract is selected when ``degree`` is present.
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    if "degree" in data or "specialization_focus" in data:
        payload = CareerAnalysisRequest.model_validate(data)
        result = ROIService(db.session).analyze_career(payload)
        return jsonify(result)

    payload = ROICalculationRequest.model_validate(data)
    result = ROIService(db.session).calculate_roi(payload, user=None)
    return jsonify(result.model_dump(mode="json"))


@blueprint.post("/analyze")
def analyze_career() -> Response:
    """Return and persist a concise, explainable education/career decision."""
    payload = CareerAnalysisRequest.model_validate(request.get_json(silent=True) or {})
    result = ROIService(db.session).analyze_career(payload)
    return jsonify(result)


@blueprint.get("/history")
@get_current_user
def roi_history(user) -> Response | str:
    logger.info("Fetching ROI history for user %s", user.id)
    if request.headers.get("HX-Request") == "true" and not request.headers.get("X-Count-Only"):
        from sqlalchemy import select, desc
        from app.models import ROICalculation
        rows = db.session.execute(
            select(ROICalculation)
            .where(ROICalculation.user_id == user.id, ROICalculation.deleted_at.is_(None))
            .order_by(desc(ROICalculation.created_at))
        ).scalars().all()
        return render_template("partials/history_table.html", calculations=rows)
        
    history = ROIService(db.session).get_history(user)
    if request.headers.get("X-Count-Only") == "true":
        return str(len(history))
        
    return jsonify([item.model_dump(mode="json") for item in history])


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
    calculation.deleted_at = datetime.now(timezone.utc)
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
