from __future__ import annotations

import hashlib
import json
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import SimulationProjection, SimulationRevision, SimulationScenario
from app.schemas import SimulationProjectionRequest


METHODOLOGY_VERSION = "scenario-projection-v1"
SALARY_BASIS = "gross_annual"
MONEY = Decimal("0.01")
PERCENT = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _percent(value: Decimal) -> Decimal:
    return value.quantize(PERCENT, rounding=ROUND_HALF_UP)


class DeterministicProjectionEngine:
    """Pure financial model; it never calls external APIs or an LLM."""

    @staticmethod
    def calculate(assumptions: dict, payload: SimulationProjectionRequest) -> dict:
        study_years = Decimal(str(assumptions["study_duration_years"]))
        annual_tuition = Decimal(str(assumptions["annual_tuition"]))
        direct_cost = (
            annual_tuition * study_years
            + payload.additional_education_cost
            + payload.incremental_living_cost
        )
        opportunity_cost = (
            payload.baseline_annual_salary
            * study_years
            * payload.foregone_income_percent
            / Decimal("100")
        )
        total_investment = direct_cost + opportunity_cost

        target_growth = payload.annual_salary_growth_percent / Decimal("100")
        baseline_growth = payload.baseline_salary_growth_percent / Decimal("100")
        cumulative = Decimal("0")
        payback_months: int | None = 0 if total_investment == 0 else None
        trajectory: list[dict] = []

        for year in range(1, payload.horizon_years + 1):
            target_salary = payload.annual_start_salary * ((Decimal("1") + target_growth) ** (year - 1))
            baseline_salary = payload.baseline_annual_salary * (
                (Decimal("1") + baseline_growth) ** (year - 1)
            )
            incremental = max(target_salary - baseline_salary, Decimal("0"))
            previous_cumulative = cumulative
            cumulative += incremental

            if payback_months is None and cumulative >= total_investment and incremental > 0:
                remaining = total_investment - previous_cumulative
                months_in_year = (remaining / (incremental / Decimal("12"))).to_integral_value(
                    rounding=ROUND_CEILING
                )
                payback_months = (year - 1) * 12 + int(months_in_year)

            trajectory.append(
                {
                    "year": year,
                    "target_salary": str(_money(target_salary)),
                    "baseline_salary": str(_money(baseline_salary)),
                    "incremental_earnings": str(_money(incremental)),
                    "cumulative_incremental_earnings": str(_money(cumulative)),
                }
            )

        roi_percent = None
        if total_investment > 0:
            roi_percent = _percent((cumulative - total_investment) / total_investment * Decimal("100"))

        evidence_metrics = {item.metric for item in payload.evidence}
        unverified_assumptions = []
        if "tuition" not in evidence_metrics:
            unverified_assumptions.append("annual_tuition")
        if "salary_growth" not in evidence_metrics and (
            payload.annual_salary_growth_percent > 0 or payload.baseline_salary_growth_percent > 0
        ):
            unverified_assumptions.append("salary_growth")

        return {
            "currency": assumptions["currency"],
            "salary_basis": SALARY_BASIS,
            "total_direct_cost": _money(direct_cost),
            "opportunity_cost": _money(opportunity_cost),
            "total_investment": _money(total_investment),
            "estimated_start_salary": _money(payload.annual_start_salary),
            "payback_months": payback_months,
            "break_even_reached": payback_months is not None,
            "horizon_years": payload.horizon_years,
            "cumulative_incremental_earnings": _money(cumulative),
            "roi_percent": roi_percent,
            "salary_trajectory": trajectory,
            "evidence": [item.model_dump(mode="json") for item in payload.evidence],
            "unverified_assumptions": unverified_assumptions,
        }


class SimulationProjectionService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def _get_revision(self, user_id: int, scenario_id: int, revision_number: int) -> SimulationRevision:
        revision = self.db.execute(
            select(SimulationRevision)
            .join(SimulationScenario)
            .where(
                SimulationScenario.id == scenario_id,
                SimulationScenario.user_id == user_id,
                SimulationRevision.revision_number == revision_number,
            )
        ).scalar_one_or_none()
        if revision is None:
            raise AppError("Ревізію сценарію не знайдено", status_code=404)
        return revision

    @staticmethod
    def _validate_evidence(assumptions: dict, payload: SimulationProjectionRequest) -> None:
        metrics = {item.metric for item in payload.evidence}
        if "target_start_salary" not in metrics:
            raise AppError("Потрібне джерело для стартової зарплати", status_code=422)
        if payload.baseline_annual_salary > 0 and "baseline_salary" not in metrics:
            raise AppError("Потрібне джерело для базової зарплати", status_code=422)

        expected_country = assumptions["country"].casefold()
        expected_currency = assumptions["currency"].upper()
        for evidence in payload.evidence:
            if evidence.country.casefold() != expected_country:
                raise AppError("Країна джерела не відповідає сценарію", status_code=422)
            if evidence.currency != expected_currency:
                raise AppError("Валюта джерела не відповідає сценарію", status_code=422)

    @staticmethod
    def _fingerprint(revision: SimulationRevision, payload: SimulationProjectionRequest) -> str:
        canonical = json.dumps(
            {
                "methodology_version": METHODOLOGY_VERSION,
                "assumptions": revision.assumptions,
                "projection_inputs": payload.model_dump(mode="json"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def create(
        self,
        user_id: int,
        scenario_id: int,
        revision_number: int,
        payload: SimulationProjectionRequest,
    ) -> tuple[SimulationProjection, bool]:
        revision = self._get_revision(user_id, scenario_id, revision_number)
        self._validate_evidence(revision.assumptions, payload)
        fingerprint = self._fingerprint(revision, payload)

        existing = self.db.execute(
            select(SimulationProjection).where(
                SimulationProjection.revision_id == revision.id,
                SimulationProjection.methodology_version == METHODOLOGY_VERSION,
                SimulationProjection.input_fingerprint == fingerprint,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing, False

        result = DeterministicProjectionEngine.calculate(revision.assumptions, payload)
        projection = SimulationProjection(
            revision_id=revision.id,
            methodology_version=METHODOLOGY_VERSION,
            input_fingerprint=fingerprint,
            **result,
        )
        self.db.add(projection)
        self.db.commit()
        self.db.refresh(projection)
        return projection, True

    def list_for_revision(
        self, user_id: int, scenario_id: int, revision_number: int
    ) -> list[SimulationProjection]:
        revision = self._get_revision(user_id, scenario_id, revision_number)
        return list(
            self.db.execute(
                select(SimulationProjection)
                .where(SimulationProjection.revision_id == revision.id)
                .order_by(SimulationProjection.created_at.desc())
            ).scalars()
        )
