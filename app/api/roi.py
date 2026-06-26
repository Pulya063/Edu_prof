from flask import Blueprint, Response, jsonify, render_template, request

from app.core.database import db
from app.core.dependencies import get_current_user, get_optional_user
from app.core.exceptions import AppError
from app.schemas import ROICalculationRequest
from app.services.roi_service import ROIService

blueprint = Blueprint("roi", __name__)


@blueprint.post("/calculate")
def calculate_roi() -> Response | str:
    payload = ROICalculationRequest.model_validate(request.get_json(silent=True) or request.form.to_dict())
    result = ROIService(db.session).calculate_roi(payload, get_optional_user())
    if request.headers.get("HX-Request") == "true":
        return render_template("partials/roi_results.html", result=result)
    return jsonify(result.model_dump(mode="json"))


@blueprint.get("/history")
def roi_history() -> Response:
    user = get_current_user()
    if not user.is_active:
        raise AppError("Inactive user", status_code=403)
    history = ROIService(db.session).get_history(user)
    return jsonify([item.model_dump(mode="json") for item in history])
