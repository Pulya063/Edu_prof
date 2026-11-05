"""Store demo calculations for one account, built only from data already in the database.

    uv run --no-sync python -m app.scripts.seed_demo_calculations --email you@example.com

Salary ranges come from the live market snapshots, inflation and the no-degree baseline from
economic_indicators (World Bank, Eurostat, State Employment Service). Run refresh_live_data first.
Tuition is 0 for state-funded full-time places and is flagged for review in every result.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select

from app.core.database import db
from app.main import app
from app.models import SimulationScenario, User
from app.schemas import ProjectionEvidence, SimulationCreateRequest, SimulationProjectionRequest
from app.services.economic_data_service import EconomicDataService
from app.services.simulation_projection_service import SimulationProjectionService
from app.services.simulation_service import SimulationService

DEMOS = [
    {"name": "Warsaw Tech · Python backend", "university": "Warsaw University of Technology", "specialization": "Computer Science",
     "country": "Poland", "currency": "PLN", "degree": "Bachelor of Engineering", "years": "3.5", "role": "Python Backend Developer"},
    {"name": "University of Warsaw · Law", "university": "University of Warsaw", "specialization": "Law",
     "country": "Poland", "currency": "PLN", "degree": "Master of Law (5-year)", "years": "5.0", "role": "Lawyer"},
    {"name": "KNU Kyiv · Law", "university": "Taras Shevchenko National University of Kyiv", "specialization": "Law",
     "country": "Ukraine", "currency": "UAH", "degree": "Bachelor of Law", "years": "4.0", "role": "Lawyer"},
    {"name": "KNU Kyiv · Python backend", "university": "Taras Shevchenko National University of Kyiv", "specialization": "Computer Science",
     "country": "Ukraine", "currency": "UAH", "degree": "Bachelor", "years": "4.0", "role": "Python Backend Developer"},
]
JOB_SEARCH_MONTHS = 3  # Stated assumption, editable in the builder; not a measured value.


def _evidence(metric: str, demo: dict, economics: dict, name: str, url: str) -> ProjectionEvidence:
    return ProjectionEvidence(
        metric=metric, source_name=name[:255], source_reference=url, acquired_at=datetime.now(UTC),
        country=demo["country"], role=demo["role"], seniority="junior", currency=demo["currency"], confidence="high",
    )


def seed(email: str) -> None:
    user = db.session.execute(select(User).where(func.lower(User.email) == email.casefold())).scalar_one()
    for demo in DEMOS:
        if db.session.execute(select(SimulationScenario.id).where(SimulationScenario.user_id == user.id, SimulationScenario.name == demo["name"])).first():
            print(f"skip {demo['name']}: already stored")
            continue
        economics = EconomicDataService(db.session).profile(demo["country"])
        inflation = economics["suggested_inflation_percent"]
        monthly_baseline = economics["baseline_monthly_wage"]
        if inflation is None or monthly_baseline is None:
            print(f"skip {demo['name']}: economic data missing, run refresh_live_data")
            continue
        inflation_series = next(series for series in economics["series"] if series["indicator"] == "cpi_inflation")

        scenario = SimulationService(db.session).create(user.id, SimulationCreateRequest.model_validate({
            "name": demo["name"],
            "assumptions": {
                "university": demo["university"], "specialization": demo["specialization"], "country": demo["country"],
                "degree": demo["degree"], "currency": demo["currency"], "annual_tuition": "0",
                "study_duration_years": demo["years"], "career_target": demo["role"], "existing_skills": [],
            },
        }))
        payload = SimulationProjectionRequest(
            market_snapshot_selection={"seniority": "junior", "minimum_confidence": "medium"},
            baseline_annual_salary=(monthly_baseline * 12).quantize(Decimal("0.01")),
            # Nominal growth equal to inflation: flat salaries in today's money on both paths.
            annual_salary_growth_percent=inflation, baseline_salary_growth_percent=inflation,
            foregone_income_percent=Decimal("100"), horizon_years=10, discount_rate_percent=Decimal("5"),
            inflation_percent=inflation, job_search_months=JOB_SEARCH_MONTHS,
            evidence=[
                _evidence("baseline_salary", demo, economics, economics["baseline_wage_source_name"], economics["baseline_wage_source_url"]),
                _evidence("inflation", demo, economics, f"{inflation_series['source_name']} (median {economics['inflation_window']})", inflation_series["source_url"]),
            ],
        )
        projection, _ = SimulationProjectionService(db.session).create(user.id, scenario.id, 1, payload)
        print(f"{demo['name']}: investment {projection.total_investment} {projection.currency}, "
              f"ROI {projection.roi_percent} %, payback {projection.payback_months} months, NPV {projection.npv}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    with app.app_context():
        seed(args.email)


if __name__ == "__main__":
    main()
