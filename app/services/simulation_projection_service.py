from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError
from app.models import (
    MarketSnapshot,
    ProjectionCost,
    ProjectionEvidenceRecord,
    ProjectionInput,
    ProjectionSource,
    ProjectionTrajectoryPoint,
    ProjectionWarning,
    SimulationProjection,
    SimulationRevision,
    SimulationScenario,
    TuitionSnapshot,
)
from app.schemas import ProjectionEvidence, SimulationProjectionRequest
from app.services.market_snapshot_service import MarketSnapshotService
from app.services.projection_ai_review_service import ProjectionAIReviewService


METHODOLOGY_VERSION = "scenario-projection-v2"
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
        if payload.annual_start_salary is None:
            raise ValueError("Projection engine requires a resolved annual_start_salary")
        study_years = Decimal(str(assumptions["study_duration_years"]))
        if assumptions.get("annual_tuition") is None:
            raise ValueError("Projection engine requires a resolved annual_tuition")
        annual_tuition = Decimal(str(assumptions["annual_tuition"]))
        tuition = annual_tuition * study_years
        gross_direct_cost = (
            tuition
            + payload.mandatory_fees
            + payload.additional_education_cost
            + payload.incremental_living_cost
        )
        direct_cost = max(
            gross_direct_cost - payload.scholarships_and_grants,
            Decimal("0"),
        )
        baseline_income_during_study = (
            payload.baseline_annual_salary
            * study_years
            * payload.foregone_income_percent
            / Decimal("100")
        )
        employment_income = payload.employment_income_during_study or Decimal("0")
        opportunity_cost = max(
            baseline_income_during_study - employment_income,
            Decimal("0"),
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
            # Negative years are material: suppressing them would overstate ROI.
            incremental = target_salary - baseline_salary
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

        evidence_by_metric = {
            metric: [item for item in payload.evidence if item.metric == metric]
            for metric in {item.metric for item in payload.evidence}
        }

        def has_supported_evidence(metric: str) -> bool:
            return any(
                item.confidence in {"medium", "high"}
                for item in evidence_by_metric.get(metric, [])
            )

        unverified_assumptions = []
        if not has_supported_evidence("tuition"):
            unverified_assumptions.append("annual_tuition")
        if not has_supported_evidence("target_start_salary"):
            unverified_assumptions.append("estimated_start_salary")
        if not has_supported_evidence("salary_growth") and (
            payload.annual_salary_growth_percent > 0 or payload.baseline_salary_growth_percent > 0
        ):
            unverified_assumptions.append("salary_growth")
        if payload.mandatory_fees > 0 and not has_supported_evidence("mandatory_fees"):
            unverified_assumptions.append("mandatory_fees")
        if payload.scholarships_and_grants > 0 and not has_supported_evidence("scholarships"):
            unverified_assumptions.append("scholarships_and_grants")
        if employment_income > 0 and not has_supported_evidence("study_income"):
            unverified_assumptions.append("employment_income_during_study")

        payback_from_enrollment_months = None
        if payback_months is not None:
            if total_investment == 0:
                payback_from_enrollment_months = 0
            else:
                study_months = int(
                    (study_years * Decimal("12")).to_integral_value(rounding=ROUND_CEILING)
                )
                payback_from_enrollment_months = study_months + payback_months

        cost_breakdown = {
            "tuition": str(_money(tuition)),
            "mandatory_fees": str(_money(payload.mandatory_fees)),
            "additional_education": str(_money(payload.additional_education_cost)),
            "incremental_living_cost": str(_money(payload.incremental_living_cost)),
            "scholarships_and_grants": str(_money(payload.scholarships_and_grants)),
            "gross_direct_cost": str(_money(gross_direct_cost)),
            "net_direct_cost": str(_money(direct_cost)),
            "baseline_income_during_study": str(_money(baseline_income_during_study)),
            "employment_income_during_study": str(_money(employment_income)),
            "opportunity_cost": str(_money(opportunity_cost)),
        }

        return {
            "currency": assumptions["currency"],
            "salary_basis": SALARY_BASIS,
            "total_direct_cost": _money(direct_cost),
            "opportunity_cost": _money(opportunity_cost),
            "total_investment": _money(total_investment),
            "estimated_start_salary": _money(payload.annual_start_salary),
            "cost_breakdown": cost_breakdown,
            "payback_months": payback_months,
            "payback_from_enrollment_months": payback_from_enrollment_months,
            "break_even_reached": payback_months is not None,
            "horizon_years": payload.horizon_years,
            "cumulative_incremental_earnings": _money(cumulative),
            "roi_percent": roi_percent,
            "salary_trajectory": trajectory,
            # Normalized DateTime columns need real datetime values; API serialization
            # converts them to ISO-8601 only at the transport boundary.
            "evidence": [item.model_dump(mode="python") for item in payload.evidence],
            "unverified_assumptions": unverified_assumptions,
        }


class SimulationProjectionService:
    """Перевірка власника → джерела з БД → evidence → deterministic engine → збереження."""
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
    def _projection_load_options() -> tuple:
        """Relationships consumed by API serializers; eager loading prevents N+1 queries."""
        return (
            selectinload(SimulationProjection.inputs),
            selectinload(SimulationProjection.costs),
            selectinload(SimulationProjection.trajectory_points),
            selectinload(SimulationProjection.evidence_records),
            selectinload(SimulationProjection.source_records),
            selectinload(SimulationProjection.warning_records),
            selectinload(SimulationProjection.ai_review),
        )

    def _resolve_salary_source(
        self, assumptions: dict, payload: SimulationProjectionRequest
    ) -> tuple[SimulationProjectionRequest, list[str]]:
        if payload.market_snapshot_id is not None:
            snapshot = MarketSnapshotService(self.db).get_validated(payload.market_snapshot_id)
        elif payload.market_snapshot_selection is not None:
            selection = payload.market_snapshot_selection
            try:
                snapshot = MarketSnapshotService(self.db).resolve_validated(
                    role=assumptions["career_target"],
                    country=assumptions["country"],
                    seniority=selection.seniority,
                    currency=assumptions["currency"],
                    as_of_date=selection.as_of_date,
                    max_age_days=selection.max_age_days,
                    minimum_confidence=selection.minimum_confidence,
                )
            except AppError as e:
                if e.status_code == 422:
                    from app.tasks.market_tasks import refresh_market_snapshot
                    role = assumptions.get("career_target", "")
                    country = assumptions.get("country", "")
                    currency = assumptions.get("currency", "")
                    refresh_market_snapshot.delay(role, country, currency)
                    raise AppError(
                        f"Дані про зарплати для '{role}' ще не завантажені. Ми почали їх оновлення — будь ласка, повторіть спробу через декілька секунд.",
                        status_code=409
                    )
                raise e
        else:
            return payload, []

        if snapshot.role.casefold() != assumptions["career_target"].casefold():
            raise AppError("Роль market snapshot не відповідає сценарію", status_code=422)
        if snapshot.country.casefold() != assumptions["country"].casefold():
            raise AppError("Країна market snapshot не відповідає сценарію", status_code=422)
        if snapshot.currency != assumptions["currency"].upper():
            raise AppError("Валюта market snapshot не відповідає сценарію", status_code=422)
        if snapshot.salary_basis != SALARY_BASIS:
            raise AppError("Salary basis market snapshot не підтримується", status_code=422)

        snapshot_evidence = ProjectionEvidence(
            metric="target_start_salary",
            source_name="Fence market snapshot",
            source_reference=f"market_snapshot:{snapshot.id}",
            acquired_at=snapshot.acquired_at,
            country=snapshot.country,
            role=snapshot.role,
            seniority=snapshot.seniority,
            currency=snapshot.currency,
            sample_size=snapshot.sample_size,
            confidence=snapshot.confidence,
        )
        resolved = payload.model_copy(
            update={
                "annual_start_salary": snapshot.median_salary,
                "evidence": [*payload.evidence, snapshot_evidence],
            }
        )
        return resolved, [str(snapshot.id)]

    def _with_tuition_evidence(
        self,
        revision: SimulationRevision,
        payload: SimulationProjectionRequest,
    ) -> SimulationProjectionRequest:
        references = [
            str(reference).split(":", 1)[1]
            for reference in revision.source_snapshot_refs
            if str(reference).startswith("tuition_snapshot:")
        ]
        if not references:
            return payload

        try:
            snapshot_id = int(references[-1])
        except ValueError as error:
            raise AppError("Некоректний tuition snapshot reference", status_code=422) from error

        snapshot = self.db.execute(
            select(TuitionSnapshot).where(
                TuitionSnapshot.id == snapshot_id,
                TuitionSnapshot.validation_status == "validated",
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise AppError("Tuition snapshot сценарію більше не доступний", status_code=422)
        if snapshot.country.casefold() != revision.assumptions["country"].casefold():
            raise AppError("Країна tuition snapshot не відповідає сценарію", status_code=422)
        if snapshot.currency != revision.assumptions["currency"].upper():
            raise AppError("Валюта tuition snapshot не відповідає сценарію", status_code=422)
        if Decimal(str(revision.assumptions["annual_tuition"])) != snapshot.annual_tuition:
            raise AppError("Tuition snapshot не відповідає збереженому tuition", status_code=422)

        reference = f"tuition_snapshot:{snapshot.id}"
        if any(item.source_reference == reference for item in payload.evidence):
            return payload
        evidence = ProjectionEvidence(
            metric="tuition",
            source_name="Fence tuition snapshot",
            source_reference=reference,
            acquired_at=snapshot.acquired_at,
            country=snapshot.country,
            role=revision.assumptions["career_target"],
            seniority=revision.assumptions["degree"],
            currency=snapshot.currency,
            confidence=snapshot.confidence,
        )
        return payload.model_copy(update={"evidence": [*payload.evidence, evidence]})

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
    def _fingerprint(
        revision: SimulationRevision,
        payload: SimulationProjectionRequest,
        source_snapshot_refs: list[str],
    ) -> str:
        canonical = json.dumps(
            {
                "methodology_version": METHODOLOGY_VERSION,
                "assumptions": revision.assumptions,
                "projection_inputs": payload.model_dump(mode="json"),
                "source_snapshot_refs": source_snapshot_refs,
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
        """Повертає прогноз і ознаку створення; повтор тих самих inputs повторно не рахуємо."""
        revision = self._get_revision(user_id, scenario_id, revision_number)
        resolved_payload, source_snapshot_refs = self._resolve_salary_source(
            revision.assumptions, payload
        )
        resolved_payload = self._with_tuition_evidence(revision, resolved_payload)
        self._validate_evidence(revision.assumptions, resolved_payload)
        fingerprint = self._fingerprint(revision, resolved_payload, source_snapshot_refs)

        existing = self.db.execute(
            select(SimulationProjection).where(
                SimulationProjection.revision_id == revision.id,
                SimulationProjection.methodology_version == METHODOLOGY_VERSION,
                SimulationProjection.input_fingerprint == fingerprint,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing, False

        result = DeterministicProjectionEngine.calculate(revision.assumptions, resolved_payload)
        cost_breakdown = result.pop("cost_breakdown")
        trajectory = result.pop("salary_trajectory")
        evidence = result.pop("evidence")
        warnings = result.pop("unverified_assumptions")
        projection = SimulationProjection(
            revision_id=revision.id,
            methodology_version=METHODOLOGY_VERSION,
            input_fingerprint=fingerprint,
            **result,
        )
        market_snapshot_id = None
        if source_snapshot_refs:
            try:
                market_snapshot_id = int(source_snapshot_refs[0])
            except (TypeError, ValueError):
                market_snapshot_id = None
        projection.inputs = ProjectionInput(
            annual_start_salary=resolved_payload.annual_start_salary,
            baseline_annual_salary=resolved_payload.baseline_annual_salary,
            annual_salary_growth_percent=resolved_payload.annual_salary_growth_percent,
            baseline_salary_growth_percent=resolved_payload.baseline_salary_growth_percent,
            foregone_income_percent=resolved_payload.foregone_income_percent,
            mandatory_fees=resolved_payload.mandatory_fees,
            scholarships_and_grants=resolved_payload.scholarships_and_grants,
            additional_education_cost=resolved_payload.additional_education_cost,
            incremental_living_cost=resolved_payload.incremental_living_cost,
            employment_income_during_study=resolved_payload.employment_income_during_study,
            horizon_years=resolved_payload.horizon_years,
            market_snapshot_id=market_snapshot_id,
            salary_source_kind="market_snapshot" if market_snapshot_id else "manual_evidence",
        )
        projection.costs = ProjectionCost(**cost_breakdown)
        projection.trajectory_points = [ProjectionTrajectoryPoint(**point) for point in trajectory]
        projection.evidence_records = [ProjectionEvidenceRecord(**item) for item in evidence]
        projection.warning_records = [ProjectionWarning(code=code) for code in warnings]
        projection.source_records = [
            ProjectionSource(
                source_kind="market_snapshot",
                reference=str(reference),
                market_snapshot_id=int(reference) if str(reference).isdigit() else None,
            )
            for reference in source_snapshot_refs
        ]
        for item in evidence:
            reference = str(item.get("source_reference", ""))
            if not reference.startswith("tuition_snapshot:"):
                continue
            try:
                tuition_snapshot_id = int(reference.split(":", 1)[1])
            except ValueError:
                continue
            projection.source_records.append(
                ProjectionSource(
                    source_kind="tuition_snapshot",
                    reference=reference,
                    tuition_snapshot_id=tuition_snapshot_id,
                )
            )
        self.db.add(projection)
        self.db.commit()
        self.db.refresh(projection)
        ProjectionAIReviewService(self.db).review_best_effort(projection, revision.assumptions)
        return projection, True

    def list_for_revision(
        self, user_id: int, scenario_id: int, revision_number: int
    ) -> list[SimulationProjection]:
        revision = self._get_revision(user_id, scenario_id, revision_number)
        return list(
            self.db.execute(
                select(SimulationProjection)
                .options(*self._projection_load_options())
                .where(SimulationProjection.revision_id == revision.id)
                .order_by(SimulationProjection.created_at.desc())
            ).scalars()
        )

    def explainability(
        self,
        user_id: int,
        scenario_id: int,
        revision_number: int,
        projection_id: int,
    ) -> dict:
        projection = self.db.execute(
            select(SimulationProjection)
            .options(*self._projection_load_options())
            .join(SimulationRevision)
            .join(SimulationScenario)
            .where(
                SimulationProjection.id == projection_id,
                SimulationRevision.revision_number == revision_number,
                SimulationScenario.id == scenario_id,
                SimulationScenario.user_id == user_id,
            )
        ).scalar_one_or_none()
        if projection is None:
            raise AppError("Проєкцію не знайдено", status_code=404)

        parsed_refs: list[int] = []
        missing_refs: list[str] = []
        market_references = [
            source.reference
            for source in projection.source_records
            if source.source_kind == "market_snapshot"
        ]
        for reference in market_references:
            try:
                parsed_refs.append(int(reference))
            except (TypeError, ValueError):
                missing_refs.append(str(reference))

        snapshots_by_id = {}
        if parsed_refs:
            snapshots = self.db.execute(
                select(MarketSnapshot).where(MarketSnapshot.id.in_(parsed_refs))
            ).scalars()
            snapshots_by_id = {snapshot.id: snapshot for snapshot in snapshots}

        source_snapshots = []
        for snapshot_id in parsed_refs:
            snapshot = snapshots_by_id.get(snapshot_id)
            if snapshot is None:
                missing_refs.append(str(snapshot_id))
                continue
            source_snapshots.append(
                {
                    "snapshot": snapshot,
                    "age_days": max((date.today() - snapshot.snapshot_date).days, 0),
                    "selected_metric": "median_salary",
                    "selected_value": snapshot.median_salary,
                }
            )

        uses_snapshot = bool(market_references)
        return {
            "projection_id": projection.id,
            "calculation_type": "deterministic",
            "ai_generated": False,
            "methodology_version": projection.methodology_version,
            "salary_basis": projection.salary_basis,
            "currency": projection.currency,
            "salary_source_kind": "market_snapshot" if uses_snapshot else "manual_evidence",
            "selected_salary_metric": "median_salary" if uses_snapshot else "annual_start_salary",
            "estimated_start_salary": projection.estimated_start_salary,
            "source_snapshots": source_snapshots,
            "source_integrity": "missing" if missing_refs else "complete",
            "missing_source_snapshot_refs": missing_refs,
            "evidence": projection.evidence,
            "unverified_assumptions": projection.unverified_assumptions,
        }

    def review_projection(
        self,
        user_id: int,
        scenario_id: int,
        revision_number: int,
        projection_id: int,
    ) -> SimulationProjection:
        """Run or retry the advisory review for an owner-scoped projection."""
        projection = self.db.execute(
            select(SimulationProjection)
            .options(*self._projection_load_options())
            .join(SimulationRevision)
            .join(SimulationScenario)
            .where(
                SimulationProjection.id == projection_id,
                SimulationRevision.revision_number == revision_number,
                SimulationScenario.id == scenario_id,
                SimulationScenario.user_id == user_id,
            )
        ).scalar_one_or_none()
        if projection is None:
            raise AppError("Проєкцію не знайдено", status_code=404)
        ProjectionAIReviewService(self.db).review_best_effort(
            projection, projection.revision.assumptions
        )
        self.db.refresh(projection)
        return projection
