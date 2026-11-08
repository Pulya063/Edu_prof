import logging
from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.core.rate_limit import rate_limit
from app.schemas import TrialProjectionOption, TrialProjectionRequest, TrialProjectionResponse
from app.services.trial_projection_service import TrialProjectionService

blueprint = Blueprint("roi", __name__)
logger = logging.getLogger(__name__)


@blueprint.get("/preview/options")
def trial_projection_options() -> Response:
    """Countries and professions the anonymous trial can calculate right now."""
    options = [TrialProjectionOption.model_validate(item).model_dump(mode="json") for item in TrialProjectionService(db.session).options()]
    return jsonify(options)


@blueprint.post("/preview")
@rate_limit(30, 60, "trial-preview")
def trial_projection_preview() -> Response:
    """Anonymous trial on the real engine and stored PL/UA data; nothing is saved."""
    payload = TrialProjectionRequest.model_validate(request.get_json(silent=True) or {})
    result = TrialProjectionResponse.model_validate(TrialProjectionService(db.session).preview(payload))
    return jsonify(result.model_dump(mode="json"))
