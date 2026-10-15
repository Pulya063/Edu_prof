"""Plan metadata and usage rules shared by the API endpoints."""

from sqlalchemy import func, select
from sqlalchemy.orm import object_session

from app.models import SimulationProjection, SimulationRevision, SimulationScenario, User

PLAN_LIMITS: dict[str, int | None] = {
    "Free": 3,
    "Pro": 30,
}

PLAN_FEATURES: dict[str, tuple[str, ...]] = {
    "Free": ("3 ROI-розрахунки", "Базовий прогноз", "Історія результатів"),
    "Pro": ("30 ROI-розрахунків", "Повний прогноз на 5 і 10 років", "AI-рекомендації"),
}


def get_plan_details(user: User) -> dict[str, object]:
    plan = user.plan if user.plan in PLAN_LIMITS else "Free"
    session = object_session(user)
    used = 0
    if session is not None:
        used = int(
            session.scalar(
                select(func.count(SimulationProjection.id))
                .join(SimulationRevision, SimulationProjection.revision_id == SimulationRevision.id)
                .join(SimulationScenario, SimulationRevision.scenario_id == SimulationScenario.id)
                .where(SimulationScenario.user_id == user.id)
            )
            or 0
        )
    limit = PLAN_LIMITS[plan]
    return {
        "name": plan,
        "limit": limit,
        "used": used,
        "remaining": None if limit is None else max(limit - used, 0),
        "features": list(PLAN_FEATURES[plan]),
    }


def has_calculation_capacity(user: User) -> bool:
    details = get_plan_details(user)
    limit = details["limit"]
    return limit is None or int(details["used"]) < int(limit)
