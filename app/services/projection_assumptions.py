"""Numbers Fence works out itself so the user does not have to guess them.

All of it is deterministic and sourced: inflation and the no-degree wage from economic_indicators, chance
of a job from the World Bank unemployment rate of people with advanced education, months of job search
from how many vacancies the salary sample found. The cost lines turn into the engine's existing inputs,
so the engine and every saved projection keep working unchanged.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.data.living_costs import COST_LABELS, LIVING_COST_KEYS, LIVING_COSTS
from app.schemas import ProjectionCostItem, ProjectionEvidence, SimulationProjectionRequest
from app.services.economic_data_service import EconomicDataService

DISCOUNT_RATE_PERCENT = Decimal("5")
MONTHS_A_YEAR = Decimal("12")


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def job_search_months(vacancies: int | None) -> int:
    """More open vacancies, shorter search. A stated rule of thumb, shown as an estimate."""
    if vacancies is None:
        return 3
    if vacancies >= 100:
        return 2
    if vacancies >= 30:
        return 3
    if vacancies >= 10:
        return 4
    return 6


class ProjectionAssumptions:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def apply_auto(self, assumptions: dict, payload: SimulationProjectionRequest) -> SimulationProjectionRequest:
        """Fill everything the user no longer types, from stored official data."""
        country, role = assumptions["country"], assumptions["career_target"]
        economics = EconomicDataService(self.db).profile(country)
        now = datetime.now(UTC)
        common = {"acquired_at": now, "country": country, "role": role, "seniority": "junior", "currency": assumptions["currency"], "confidence": "high"}
        evidence = list(payload.evidence)
        update: dict[str, Any] = {"foregone_income_percent": Decimal("100"), "discount_rate_percent": DISCOUNT_RATE_PERCENT}

        inflation = economics.get("suggested_inflation_percent")
        if inflation is not None:
            inflation = Decimal(str(inflation))
            # Salaries grow with inflation on both paths: results stay in today's money.
            growth = min(max(inflation, Decimal("0")), Decimal("50"))
            update.update(inflation_percent=inflation, annual_salary_growth_percent=growth, baseline_salary_growth_percent=growth)
            series = next((item for item in economics.get("series", []) if item.get("indicator") == "cpi_inflation"), {})
            evidence.append(ProjectionEvidence(metric="inflation", source_name=f"{series.get('source_name') or 'CPI inflation'} (median {economics.get('inflation_window') or 'recent years'})"[:255],
                                               source_reference=series.get("source_url") or "economic_indicators:cpi_inflation", **common))
            evidence.append(ProjectionEvidence(metric="salary_growth", source_name="Salaries grow with inflation on both paths", source_reference="fence:real-terms", **common))

        monthly = economics.get("baseline_monthly_wage")
        if payload.baseline_annual_salary == 0 and monthly is not None:
            update["baseline_annual_salary"] = _money(Decimal(str(monthly)) * MONTHS_A_YEAR)
            evidence.append(ProjectionEvidence(metric="baseline_salary", source_name=str(economics.get("baseline_wage_source_name") or "Official wage statistics")[:255],
                                               source_reference=economics.get("baseline_wage_source_url") or "economic_indicators:baseline_wage", **common))

        unemployment = economics.get("graduate_unemployment_percent")
        if unemployment is not None:
            update["employment_probability_percent"] = _money(Decimal("100") - Decimal(str(unemployment)))
        vacancies = next((item.sample_size for item in payload.evidence if item.metric == "target_start_salary"), None)
        update["job_search_months"] = job_search_months(vacancies)
        update["evidence"] = evidence
        return payload.model_copy(update=update)

    def build_items(self, assumptions: dict, payload: SimulationProjectionRequest) -> list[ProjectionCostItem]:
        """Every line, each on its own: what the user typed, otherwise the country average."""
        years = Decimal(str(assumptions["study_duration_years"]))
        given = {item.key: item for item in payload.cost_items}
        tuition = Decimal(str(assumptions.get("annual_tuition") or 0)) * years
        pay = payload.baseline_annual_salary * years
        items: list[ProjectionCostItem] = []

        def add(key: str, amount: Decimal, source: str, **extra: Any) -> None:
            items.append(given.get(key) or ProjectionCostItem(key=key, label=COST_LABELS[key], amount=_money(amount), source=source, **extra))

        add("tuition", tuition, "calculated")
        add("mandatory_fees", payload.mandatory_fees, "user")
        averages = LIVING_COSTS.get(assumptions["country"])
        for key in LIVING_COST_KEYS:
            monthly = Decimal(str(averages["lines"].get(key, 0))) if averages else Decimal("0")
            if key in given:
                items.append(given[key])
            elif monthly:
                items.append(ProjectionCostItem(key=key, label=averages.get("labels", {}).get(key, COST_LABELS[key]), amount=_money(monthly * MONTHS_A_YEAR * years), per_month=monthly,
                                                source="country_average", source_name=averages["source_name"], source_url=averages["source_url"]))
        add("additional_training", payload.additional_education_cost, "user")
        add("scholarships", payload.scholarships_and_grants, "user")
        add("pay_given_up", pay, "calculated", editable=False)
        add("income_during_study", payload.employment_income_during_study or Decimal("0"), "user")
        return items

    @staticmethod
    def to_engine_inputs(assumptions: dict, payload: SimulationProjectionRequest, items: list[ProjectionCostItem]) -> tuple[dict, SimulationProjectionRequest]:
        """Lines turned into the engine's inputs; a switched-off line counts as nothing."""
        years = Decimal(str(assumptions["study_duration_years"]))

        def amount(*keys: str) -> Decimal:
            return sum((item.amount for item in items if item.key in keys and item.enabled), Decimal("0"))

        engine_assumptions = {**assumptions, "annual_tuition": amount("tuition") / years}
        pay_on = any(item.key == "pay_given_up" and item.enabled for item in items)
        income = amount("income_during_study")
        engine_payload = payload.model_copy(update={
            "mandatory_fees": amount("mandatory_fees"),
            "incremental_living_cost": amount(*LIVING_COST_KEYS),
            "additional_education_cost": amount("additional_training"),
            "scholarships_and_grants": amount("scholarships"),
            "employment_income_during_study": income if income else None,
            "foregone_income_percent": payload.foregone_income_percent if pay_on else Decimal("0"),
            "cost_items": items,
        })
        return engine_assumptions, engine_payload
