"""Anonymous trial calculation on the real engine and stored data, without saving anything.

Same inputs the demo seed uses for a full scenario: the validated junior market snapshot for the
role and country, the no-degree baseline and inflation from economic_indicators, salaries growing
with inflation (today's money). Missing data is reported as an error, never filled with a guess.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import MarketSnapshot
from app.schemas import MarketSnapshotSelection, ProjectionEvidence, SimulationProjectionRequest, TrialProjectionRequest
from app.services.economic_data_service import EconomicDataService
from app.services.market_ingestion_service import SUPPORTED_ROLES
from app.services.market_snapshot_service import MarketSnapshotService
from app.services.official_wage_service import METHODOLOGY_VERSION as OFFICIAL_METHODOLOGY
from app.services.simulation_projection_service import METHODOLOGY_VERSION, DeterministicProjectionEngine

logger = logging.getLogger(__name__)

COUNTRY_CURRENCY = {"Poland": "PLN", "Ukraine": "UAH"}
TRIAL_HORIZON_YEARS = 10
TRIAL_DISCOUNT_RATE = Decimal("5")
TRIAL_SELECTION = {"seniority": "junior", "minimum_confidence": "medium"}

# State-funded places unless a tuition is stated; the 5-year target is an example for the landing.
SHOWCASE_SCENARIOS = (
    ("warsaw-python", "Warsaw Tech · Python", {"country": "Poland", "career_target": "Python Backend Developer", "university": "Warsaw University of Technology", "study_years": Decimal("3.5"), "target_payback_years": 5}),
    ("knu-python", "KNU Kyiv · Python", {"country": "Ukraine", "career_target": "Python Backend Developer", "university": "Taras Shevchenko National University of Kyiv", "study_years": Decimal("4"), "target_payback_years": 5}),
    ("warsaw-law", "Univ. of Warsaw · Law", {"country": "Poland", "career_target": "Lawyer", "university": "University of Warsaw", "study_years": Decimal("5"), "target_payback_years": 5}),
    ("poland-nurse", "Nurse · Poland", {"country": "Poland", "career_target": "Nurse", "study_years": Decimal("3.5"), "target_payback_years": 5}),
    ("ukraine-teacher", "Teacher · Ukraine", {"country": "Ukraine", "career_target": "Teacher", "study_years": Decimal("4"), "target_payback_years": 5}),
)
SHOWCASE_GRANT = Decimal("30000")
SHOWCASE_GRANT_REQUEST = {"country": "Poland", "career_target": "Python Backend Developer", "study_years": Decimal("3.5"), "annual_tuition": Decimal("20000"), "target_payback_years": 5}


def _snapshot_source_name(snapshot: MarketSnapshot) -> str:
    """The snapshot's own first source (job board, survey or Eurostat), so the visitor sees where it came from."""
    names = [str(item.get("name")) for item in (snapshot.sources or []) if isinstance(item, dict) and item.get("name")]
    level = "" if snapshot.seniority == "junior" or (names and "all-level" in names[0]) else f", {snapshot.seniority}"
    return (f"{names[0]}{level}" if names else "Fence market snapshot")[:255]


class TrialProjectionService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def showcase(self) -> dict:
        """Fixed example scenarios for the public landing, calculated by the same engine."""
        scenarios = []
        for key, label, request in SHOWCASE_SCENARIOS:
            try:
                scenarios.append({"key": key, "label": label, "result": self.preview(TrialProjectionRequest(**request))})
            except AppError as error:
                logger.info("Showcase scenario %s skipped: %s", key, error)
        grant_example = None
        try:
            request = TrialProjectionRequest(**SHOWCASE_GRANT_REQUEST)
            grant_example = {
                "label": "Warsaw · Python backend, 3.5 years",
                "grant": SHOWCASE_GRANT,
                "without_grant": self.preview(request),
                "with_grant": self.preview(request, scholarships=SHOWCASE_GRANT),
            }
        except AppError as error:
            logger.info("Showcase grant example skipped: %s", error)
        return {"careers": self.options(), "scenarios": scenarios, "grant_example": grant_example}

    def options(self) -> list[dict]:
        """Role/country pairs the preview can calculate now: the snapshot it would pick for each pair."""
        rows = self.db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.validation_status == "validated", MarketSnapshot.country.in_(COUNTRY_CURRENCY),
                   MarketSnapshot.confidence.in_(("medium", "high")))
        ).scalars()
        best: dict[tuple[str, str], MarketSnapshot] = {}
        rank = {"high": 3, "medium": 2}
        for snapshot in rows:
            if snapshot.role not in SUPPORTED_ROLES or snapshot.currency != COUNTRY_CURRENCY[snapshot.country]:
                continue
            # Same order as MarketSnapshotService.resolve_validated: exact junior level, newest, most confident.
            key = (snapshot.country, snapshot.role)
            order = (snapshot.seniority == TRIAL_SELECTION["seniority"], snapshot.snapshot_date, rank[snapshot.confidence], snapshot.sample_size or 0, snapshot.id)
            current = best.get(key)
            if current is None or order > (current.seniority == TRIAL_SELECTION["seniority"], current.snapshot_date, rank[current.confidence], current.sample_size or 0, current.id):
                best[key] = snapshot
        return sorted(({
            "country": snapshot.country,
            "currency": snapshot.currency,
            "career_target": snapshot.role,
            "median_salary": snapshot.median_salary,
            "seniority": snapshot.seniority,
            "salary_source": "official" if snapshot.methodology_version == OFFICIAL_METHODOLOGY else "listings",
        } for snapshot in best.values()), key=lambda item: (item["country"], item["career_target"]))

    def preview(self, payload: TrialProjectionRequest, scholarships: Decimal = Decimal("0")) -> dict:
        role = next((name for name in SUPPORTED_ROLES if name.casefold() == payload.career_target.strip().casefold()), None)
        if role is None:
            raise AppError("There is no salary data for this role yet", status_code=422)
        currency = COUNTRY_CURRENCY[payload.country]
        selection = MarketSnapshotSelection(**TRIAL_SELECTION)
        try:
            snapshot = MarketSnapshotService(self.db).resolve_validated(
                role=role, country=payload.country, currency=currency, seniority=selection.seniority,
                as_of_date=selection.as_of_date, max_age_days=selection.max_age_days,
                minimum_confidence=selection.minimum_confidence,
            )
        except AppError as error:
            raise AppError("Salary data for this role and country is unavailable right now", status_code=422) from error

        economics = EconomicDataService(self.db).profile(payload.country)
        inflation = economics.get("suggested_inflation_percent")
        monthly_baseline = economics.get("baseline_monthly_wage")
        if inflation is None or monthly_baseline is None:
            raise AppError("Economic data for this country is not loaded yet", status_code=422)
        baseline_annual = (Decimal(str(monthly_baseline)) * 12).quantize(Decimal("0.01"))
        inflation = Decimal(str(inflation))

        now = datetime.now(UTC)
        inflation_series = next((series for series in economics.get("series", []) if series.get("indicator") == "cpi_inflation"), {})
        evidence = [
            ProjectionEvidence(
                metric="target_start_salary", source_name=_snapshot_source_name(snapshot), source_reference=f"market_snapshot:{snapshot.id}",
                acquired_at=snapshot.acquired_at, country=snapshot.country, role=snapshot.role, seniority=snapshot.seniority,
                currency=snapshot.currency, sample_size=snapshot.sample_size, confidence=snapshot.confidence,
            ),
            ProjectionEvidence(
                metric="baseline_salary", source_name=str(economics.get("baseline_wage_source_name") or "Official wage statistics")[:255],
                source_reference=economics.get("baseline_wage_source_url") or "economic_indicators:baseline_wage", acquired_at=now, country=payload.country,
                role=role, seniority="junior", currency=currency, confidence="high",
            ),
            ProjectionEvidence(
                metric="inflation", source_name=f"{inflation_series.get('source_name') or 'CPI inflation'} (median {economics.get('inflation_window') or 'recent years'})"[:255],
                source_reference=inflation_series.get("source_url") or "economic_indicators:cpi_inflation",
                acquired_at=now, country=payload.country, role=role, seniority="junior", currency=currency, confidence="high",
            ),
        ]
        request = SimulationProjectionRequest(
            annual_start_salary=snapshot.median_salary,
            baseline_annual_salary=baseline_annual,
            # Growth equal to inflation on both paths: flat salaries in today's money.
            annual_salary_growth_percent=inflation, baseline_salary_growth_percent=inflation,
            foregone_income_percent=Decimal("100"), horizon_years=TRIAL_HORIZON_YEARS,
            discount_rate_percent=TRIAL_DISCOUNT_RATE, inflation_percent=inflation,
            job_search_months=payload.job_search_months, target_payback_years=payload.target_payback_years,
            scholarships_and_grants=scholarships,
            evidence=evidence,
        )
        assumptions = {
            "currency": currency, "country": payload.country, "career_target": role,
            "study_duration_years": payload.study_years, "annual_tuition": payload.annual_tuition,
        }
        result = DeterministicProjectionEngine.calculate(assumptions, request, (snapshot.salary_min, snapshot.salary_max))

        return {
            "methodology_version": METHODOLOGY_VERSION,
            "country": payload.country,
            "career_target": role,
            "university": payload.university or None,
            "currency": currency,
            "study_years": payload.study_years,
            "annual_tuition": payload.annual_tuition,
            "total_direct_cost": result["total_direct_cost"],
            "opportunity_cost": result["opportunity_cost"],
            "total_investment": result["total_investment"],
            "estimated_start_salary": result["estimated_start_salary"],
            "baseline_annual_salary": baseline_annual,
            "inflation_percent": inflation,
            "job_search_months": payload.job_search_months,
            "horizon_years": TRIAL_HORIZON_YEARS,
            "roi_percent": result["roi_percent"],
            "payback_months": result["payback_months"],
            "payback_from_enrollment_months": result["payback_from_enrollment_months"],
            "target_payback_years": result["target_payback_years"],
            "payback_within_target": result["payback_within_target"],
            "payback_target_gap_months": result["payback_target_gap_months"],
            "scenarios": [
                {
                    "scenario": item["scenario"],
                    "start_salary": Decimal(item["start_salary"]),
                    "roi_percent": None if item["roi_percent"] is None else Decimal(item["roi_percent"]),
                    "payback_months": item["payback_months"],
                }
                for item in result["scenario_outcomes"]
            ],
            "trajectory": [
                {
                    "year": point["year"],
                    "target_salary": Decimal(str(point["target_salary"])).quantize(Decimal("0.01")),
                    "baseline_salary": Decimal(str(point["baseline_salary"])).quantize(Decimal("0.01")),
                    "cumulative_incremental_earnings": Decimal(str(point["cumulative_incremental_earnings"])).quantize(Decimal("0.01")),
                }
                for point in result["salary_trajectory"]
            ],
            "sources": [
                {
                    "metric": item.metric, "source_name": item.source_name, "source_reference": item.source_reference,
                    "sample_size": item.sample_size, "confidence": item.confidence,
                }
                for item in evidence
            ],
        }
