from __future__ import annotations

import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import TrialROIRequest
from app.core.logging_config import log_call
from app.services.market_data_service import MarketDataService


logger = logging.getLogger(__name__)

DEFAULT_COUNTRY = "United States"


class ROIService:
    """Legacy trial preview and read-only history; new results use simulations."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.market_service = MarketDataService()

    @log_call
    def analyze_trial(self, payload: TrialROIRequest) -> dict:
        """Lightweight analysis for trial without full projections and DB saving."""
        prospects = self.market_service.predict_career_prospects(payload.faculty, DEFAULT_COUNTRY)
        start_salary = float(prospects.get("expected_start_salary"))

        total_investment = float(payload.annual_tuition * payload.study_years)

        realistic_monthly = start_salary / 12.0
        payback_months = max(1, int(round(total_investment / realistic_monthly))) if realistic_monthly > 0 else 1200
        first_year_roi = (((realistic_monthly * 0.95 * 12 - total_investment) / total_investment) * 100) if total_investment > 0 else 0

        return {
            "education": {
                "specialization": payload.faculty,
                "total_investment": {"min": round(total_investment, 2)},
                "total_education_cost": {"min": round(total_investment, 2)},
            },
            "roi": {
                "payback_months": {"min": payback_months},
                "first_year_roi_percent": {"min": round(first_year_roi, 2)},
                "roi_percent": {"min": round(first_year_roi, 2)},
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

