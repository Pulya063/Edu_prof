"""Plan metadata and usage rules shared by the API endpoints."""

from sqlalchemy import func, select
from sqlalchemy.orm import object_session

from app.models import SimulationScenario, User

PLAN_LIMITS: dict[str, int | None] = {
    "Free": 3,
    "Pro": 30,
    "Plus": 100,
    "Teams": None,
}

PLAN_FEATURES: dict[str, tuple[str, ...]] = {
    "Free": ("3 saved calculations", "10-year forecast", "Result history"),
    "Pro": ("30 saved calculations", "10-year forecast", "AI review"),
    "Plus": ("100 saved calculations", "Advanced scenario comparison", "AI review"),
    "Teams": ("Unlimited calculations", "Shared scenario library", "AI review"),
}


def get_plan_details(user: User) -> dict[str, object]:
    """Saved calculations (scenarios) against the plan's limit; admins have no limit."""
    plan = user.plan if user.plan in PLAN_LIMITS else "Free"
    session = object_session(user)
    used = 0
    if session is not None:
        used = int(session.scalar(select(func.count(SimulationScenario.id)).where(SimulationScenario.user_id == user.id)) or 0)
    limit = None if user.is_admin else PLAN_LIMITS[plan]
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
