from flask import Blueprint, Response, g, jsonify, render_template, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import ROICalculationRequest
from app.services.external_api import get_tuition_history, search_universities
from app.services.roi_service import ROIService

blueprint = Blueprint("roi", __name__)


# ── ROI калькулятор ───────────────────────────────────────────────────────────

@blueprint.post("/calculate")
@get_current_user
def calculate_roi(user: User) -> Response | str:
    payload = ROICalculationRequest.model_validate(
        request.get_json(silent=True) or request.form.to_dict()
    )
    result = ROIService(db.session).calculate_roi(payload, user)
    if request.headers.get("HX-Request") == "true":
        return render_template("partials/roi_results.html", result=result)
    return jsonify(result.model_dump(mode="json"))


@blueprint.get("/history")
@get_current_user
def roi_history(user, **kwargs) -> Response:
    history = ROIService(db.session).get_history(user)
    return jsonify([item.model_dump(mode="json") for item in history])


# ── Пошук університетів ───────────────────────────────────────────────────────

@blueprint.get("/universities/search")
def universities_search() -> Response:
    """
    GET /api/roi/universities/search?q=Harvard
    Повертає список університетів з Hipolabs + College Scorecard (USA).
    """
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify([])
    results = search_universities(query)
    return jsonify(results)


# ── Вартість навчання по роках ────────────────────────────────────────────────

@blueprint.get("/universities/tuition")
def universities_tuition() -> Response:
    """
    GET /api/roi/universities/tuition?scorecard_id=123456&country=Ukraine
    Повертає вартість навчання по роках (2018–2023).

    - scorecard_id — ID з College Scorecard (для університетів США)
    - country      — назва країни (для вбудованого словника)
    """
    raw_id  = request.args.get("scorecard_id")
    country = (request.args.get("country") or "").strip()

    scorecard_id = int(raw_id) if raw_id and raw_id.isdigit() else None

    if not scorecard_id and not country:
        return jsonify({"error": "Потрібен scorecard_id або country"}), 400

    history = get_tuition_history(scorecard_id, country)
    return jsonify(history)