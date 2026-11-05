from __future__ import annotations

import logging
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import SimulationProjectionRequest, TrialROIRequest
from app.core.logging_config import log_call
from app.services.market_data_service import MarketDataService
from app.services.simulation_projection_service import METHODOLOGY_VERSION, DeterministicProjectionEngine


logger = logging.getLogger(__name__)

DEFAULT_COUNTRY = "United States"
TRIAL_HORIZON_YEARS = 10
TRIAL_NOTE = (
    "Rough preview: dataset start salary, no baseline income, no salary growth or scenarios. "
    "Create a scenario for a sourced forecast."
)


class ROIService:
    """Legacy trial preview and read-only history; new results use simulations."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.market_service = MarketDataService()

    @log_call
    def analyze_trial(self, payload: TrialROIRequest) -> dict:
        """Rough preview on the same deterministic engine as simulations, but with a dataset salary,
        no baseline income and no growth, so it is not a saved or evidence-backed forecast."""
        prospects = self.market_service.predict_career_prospects(payload.faculty, DEFAULT_COUNTRY)
        start_salary = Decimal(str(prospects.get("expected_start_salary"))).quantize(Decimal("0.01"))
        request = SimulationProjectionRequest(
            annual_start_salary=start_salary,
            baseline_annual_salary=Decimal("0"),
            horizon_years=TRIAL_HORIZON_YEARS,
        )
        result = DeterministicProjectionEngine.calculate(
            {
                "currency": "USD",
                "study_duration_years": payload.study_years,
                "annual_tuition": payload.annual_tuition,
            },
            request,
        )
        total_investment = result["total_investment"]
        first_year = Decimal(result["salary_trajectory"][0]["incremental_earnings"])
        first_year_roi = (
            (first_year - total_investment) / total_investment * Decimal("100") if total_investment > 0 else Decimal("0")
        )

        return {
            "preview": "rough",
            "methodology_version": METHODOLOGY_VERSION,
            "horizon_years": TRIAL_HORIZON_YEARS,
            "note": TRIAL_NOTE,
            "education": {
                "specialization": payload.faculty,
                "total_investment": {"min": float(total_investment)},
                "total_education_cost": {"min": float(total_investment)},
            },
            "roi": {
                "payback_months": {"min": result["payback_months"]},
                "first_year_roi_percent": {"min": float(round(first_year_roi, 2))},
                "roi_percent": {"min": float(result["roi_percent"] or 0)},
            },
        }

    @log_call
    def get_full_history(self, user: User) -> list[dict]:
        """Return a chronologically sorted list of all simulation projections for the user."""
        from app.models import SimulationScenario, SimulationRevision, SimulationProjection

        items: list[dict] = []

        projections = self.db.execute(
            select(SimulationProjection, SimulationRevision, SimulationScenario)
            .join(SimulationRevision, SimulationProjection.revision_id == SimulationRevision.id)
            .join(SimulationScenario, SimulationRevision.scenario_id == SimulationScenario.id)
            .where(SimulationScenario.user_id == user.id)
            .order_by(desc(SimulationProjection.created_at))
        ).all()

        for p, rev, scen in projections:
            assumptions = rev.assumptions
            items.append({
                "id": p.id,
                "source": "simulation_projection",
                "university": assumptions.get("university"),
                "specialization": assumptions.get("specialization") or assumptions.get("career_target"),
                "degree": assumptions.get("degree"),
                "country": assumptions.get("country"),
                "study_years": float(assumptions.get("study_duration_years", 4.0)),
                "total_investment_min": float(p.total_investment),
                "total_investment_max": float(p.total_investment),
                "roi_first_year_min": float(p.roi_percent) if p.roi_percent is not None else None,
                "roi_first_year_max": float(p.roi_percent) if p.roi_percent is not None else None,
                "payback_months_min": p.payback_months,
                "payback_months_max": p.payback_months,
                "payback_likely": p.break_even_reached,
                "long_term_roi": None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })

        return items

