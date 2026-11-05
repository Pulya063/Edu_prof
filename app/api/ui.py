"""Lightweight server-rendered UI (Jinja) over the existing JSON API.

Pages are GET-only; every mutation goes through /api/* from ui.js with the CSRF header,
so this module adds no business logic of its own.
"""

from flask import Blueprint, Response, g, redirect, render_template

from app.core.database import db
from app.core.exceptions import AppError
from app.schemas import SimulationProjectionResponse, SimulationScenarioSummary
from app.services.simulation_projection_service import SimulationProjectionService
from app.services.simulation_service import SimulationService

blueprint = Blueprint("ui", __name__)


def _require_user():
    return getattr(g, "user", None)


@blueprint.get("/login")
def login_page() -> str | Response:
    if _require_user():
        return redirect("/ui/")
    return render_template("ui/login.html")


@blueprint.get("/")
def scenarios_page() -> str | Response:
    user = _require_user()
    if not user:
        return redirect("/ui/login")
    scenarios = [
        SimulationScenarioSummary.model_validate(item).model_dump(mode="json")
        for item in SimulationService(db.session).list_for_user(user.id)
    ]
    return render_template("ui/scenarios.html", user=user, scenarios=scenarios)


@blueprint.get("/new")
def new_scenario_page() -> str | Response:
    user = _require_user()
    if not user:
        return redirect("/ui/login")
    return render_template("ui/new.html", user=user)


@blueprint.get("/scenarios/<int:scenario_id>")
def scenario_page(scenario_id: int) -> str | Response:
    user = _require_user()
    if not user:
        return redirect("/ui/login")
    try:
        scenario = SimulationService(db.session).get(user.id, scenario_id)
    except AppError:
        return render_template("ui/not_found.html", user=user), 404
    revision = next(
        (item for item in scenario.revisions if item.revision_number == scenario.current_revision_number),
        scenario.revisions[-1],
    )
    projections = SimulationProjectionService(db.session).list_for_revision(
        user.id, scenario.id, scenario.current_revision_number
    )
    projection = (
        SimulationProjectionResponse.model_validate(projections[0]).model_dump(mode="json")
        if projections
        else None
    )
    return render_template(
        "ui/scenario.html",
        user=user,
        scenario=scenario,
        assumptions=revision.assumptions,
        projection=projection,
    )
