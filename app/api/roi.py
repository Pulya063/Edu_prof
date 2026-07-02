from flask import Blueprint, Response, g, jsonify, render_template, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import ROICalculationRequest
from app.services.roi_service import ROIService

blueprint = Blueprint("roi", __name__)


# @blueprint.post повинен бути БЛИЖЧИМ до функції, @get_current_user — зовнішнім
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
def roi_history(user: User) -> Response:
    history = ROIService(db.session).get_history(user)
    return jsonify([item.model_dump(mode="json") for item in history])
