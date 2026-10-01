from flask import Blueprint, Response, jsonify, request

from app.core.database import db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import (
    SimulationCreateRequest,
    SimulationOverviewResponse,
    SimulationRevisionCreateRequest,
    SimulationProjectionRequest,
    SimulationProjectionExplainabilityResponse,
    SimulationProjectionResponse,
    SimulationScenarioResponse,
    SimulationScenarioSummary,
)
from app.services.simulation_service import SimulationService
from app.services.simulation_projection_service import SimulationProjectionService

blueprint = Blueprint("simulations", __name__)


@blueprint.post("")
@get_current_user
def create_simulation(user: User) -> tuple[Response, int]:
    payload = SimulationCreateRequest.model_validate(request.get_json(silent=True) or {})
    scenario = SimulationService(db.session).create(user.id, payload)
    response = SimulationScenarioResponse.model_validate(scenario)
    return jsonify(response.model_dump(mode="json")), 201


@blueprint.get("")
@get_current_user
def list_simulations(user: User) -> Response:
    scenarios = SimulationService(db.session).list_for_user(user.id)
    response = [SimulationScenarioSummary.model_validate(item).model_dump(mode="json") for item in scenarios]
    return jsonify(response)


@blueprint.get("/overview")
@get_current_user
def get_simulation_overview(user: User) -> Response:
    simulation_service = SimulationService(db.session)
    scenarios = simulation_service.list_for_user(user.id)
    if not scenarios:
        response = SimulationOverviewResponse(status="empty")
        return jsonify(response.model_dump(mode="json"))

    scenario = simulation_service.get(user.id, scenarios[0].id)
    projection_service = SimulationProjectionService(db.session)
    projections = projection_service.list_for_revision(
        user.id,
        scenario.id,
        scenario.current_revision_number,
    )
    if not projections:
        response = SimulationOverviewResponse(status="scenario_only", scenario=scenario)
        return jsonify(response.model_dump(mode="json"))

    projection = projections[0]
    explainability = projection_service.explainability(
        user.id,
        scenario.id,
        scenario.current_revision_number,
        projection.id,
    )
    response = SimulationOverviewResponse(
        status="projected",
        scenario=scenario,
        projection=projection,
        explainability=explainability,
    )
    return jsonify(response.model_dump(mode="json"))


@blueprint.get("/<int:scenario_id>")
@get_current_user
def get_simulation(scenario_id: int, user: User) -> Response:
    scenario = SimulationService(db.session).get(user.id, scenario_id)
    response = SimulationScenarioResponse.model_validate(scenario)
    return jsonify(response.model_dump(mode="json"))


@blueprint.post("/<int:scenario_id>/revisions")
@get_current_user
def create_simulation_revision(scenario_id: int, user: User) -> tuple[Response, int]:
    payload = SimulationRevisionCreateRequest.model_validate(request.get_json(silent=True) or {})
    scenario = SimulationService(db.session).add_revision(user.id, scenario_id, payload)
    response = SimulationScenarioResponse.model_validate(scenario)
    return jsonify(response.model_dump(mode="json")), 201


@blueprint.post("/<int:scenario_id>/revisions/<int:revision_number>/projections")
@get_current_user
def create_simulation_projection(
    scenario_id: int, revision_number: int, user: User
) -> tuple[Response, int]:
    payload = SimulationProjectionRequest.model_validate(request.get_json(silent=True) or {})
    projection, created = SimulationProjectionService(db.session).create(
        user.id, scenario_id, revision_number, payload
    )
    response = SimulationProjectionResponse.model_validate(projection)
    return jsonify(response.model_dump(mode="json")), 201 if created else 200


@blueprint.get("/<int:scenario_id>/revisions/<int:revision_number>/projections")
@get_current_user
def list_simulation_projections(scenario_id: int, revision_number: int, user: User) -> Response:
    projections = SimulationProjectionService(db.session).list_for_revision(
        user.id, scenario_id, revision_number
    )
    response = [
        SimulationProjectionResponse.model_validate(item).model_dump(mode="json")
        for item in projections
    ]
    return jsonify(response)


@blueprint.get(
    "/<int:scenario_id>/revisions/<int:revision_number>/projections/<int:projection_id>/explainability"
)
@get_current_user
def get_simulation_projection_explainability(
    scenario_id: int,
    revision_number: int,
    projection_id: int,
    user: User,
) -> Response:
    explanation = SimulationProjectionService(db.session).explainability(
        user.id,
        scenario_id,
        revision_number,
        projection_id,
    )
    response = SimulationProjectionExplainabilityResponse.model_validate(explanation)
    return jsonify(response.model_dump(mode="json"))
