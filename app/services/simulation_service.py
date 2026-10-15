from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError
from app.models import SimulationRevision, SimulationScenario, TuitionSnapshot
from app.schemas import (
    SimulationAssumptions,
    SimulationCreateRequest,
    SimulationRevisionCreateRequest,
    TuitionSnapshotSelection,
)
from app.services.tuition_snapshot_service import TuitionSnapshotService


class SimulationService:
    """Керує умовами сценарію та його ревізіями; фінансовий розрахунок виконується окремо."""
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def _resolve_tuition(
        self,
        assumptions: SimulationAssumptions,
        snapshot_id: int | None,
        selection: TuitionSnapshotSelection | None,
    ) -> tuple[SimulationAssumptions, list[str]]:
        if snapshot_id is None and selection is None:
            return assumptions, []

        if snapshot_id is not None:
            snapshot = TuitionSnapshotService(self.db).get_validated(snapshot_id)
        else:
            assert selection is not None
            expected = {
                "university": assumptions.university,
                "program": assumptions.specialization,
                "country": assumptions.country,
                "currency": assumptions.currency,
            }
            actual = {
                "university": selection.university,
                "program": selection.program,
                "country": selection.country,
                "currency": selection.currency,
            }
            if any(actual[key].casefold() != value.casefold() for key, value in expected.items()):
                raise AppError("Tuition selection не відповідає assumptions сценарію", status_code=422)
            try:
                snapshot = TuitionSnapshotService(self.db).resolve_validated(selection)
            except AppError as e:
                if e.status_code == 422 and selection.university and selection.country.casefold() == "united states":
                    from app.services.tuition_ingestion_service import CollegeScorecardTuitionProvider
                    from app.tasks.tuition_tasks import refresh_college_scorecard_tuition
                    from app.core.watched_universities import add_watched_scorecard_id
                    
                    provider = CollegeScorecardTuitionProvider()
                    scorecard_id = provider.search_institution(selection.university)
                    if scorecard_id:
                        refresh_college_scorecard_tuition.delay(scorecard_id)
                        add_watched_scorecard_id(scorecard_id)
                        raise AppError(
                            f"Дані для '{selection.university}' ще не завантажені. Ми почали їх оновлення — будь ласка, повторіть спробу через декілька секунд.",
                            status_code=409
                        )
                raise e

        self._validate_tuition_snapshot(assumptions, snapshot)
        resolved = assumptions.model_copy(update={"annual_tuition": snapshot.annual_tuition})
        return resolved, [f"tuition_snapshot:{snapshot.id}"]

    @staticmethod
    def _validate_tuition_snapshot(
        assumptions: SimulationAssumptions, snapshot: TuitionSnapshot
    ) -> None:
        if snapshot.country.casefold() != assumptions.country.casefold():
            raise AppError("Країна tuition snapshot не відповідає сценарію", status_code=422)
        if snapshot.currency != assumptions.currency.upper():
            raise AppError("Валюта tuition snapshot не відповідає сценарію", status_code=422)
        if snapshot.scope in {"program", "university"}:
            if not snapshot.university or snapshot.university.casefold() != assumptions.university.casefold():
                raise AppError("Університет tuition snapshot не відповідає сценарію", status_code=422)
        if snapshot.scope == "program":
            if not snapshot.program or snapshot.program.casefold() != assumptions.specialization.casefold():
                raise AppError("Програма tuition snapshot не відповідає сценарію", status_code=422)

    def create(self, user_id: int, payload: SimulationCreateRequest) -> SimulationScenario:
        """Визначити tuition з локальних даних і зберегти сценарій з першою ревізією."""
        resolved_assumptions, source_refs = self._resolve_tuition(
            payload.assumptions,
            payload.tuition_snapshot_id,
            payload.tuition_snapshot_selection,
        )
        assumptions = resolved_assumptions.model_dump(mode="json")
        scenario = SimulationScenario(
            user_id=user_id,
            name=payload.name,
            target_role=resolved_assumptions.career_target,
            country=resolved_assumptions.country,
            currency=resolved_assumptions.currency,
        )
        scenario.revisions.append(
            SimulationRevision(
                revision_number=1,
                assumptions=assumptions,
                methodology_version="scenario-foundation-v2",
                source_snapshot_refs=source_refs,
            )
        )
        self.db.add(scenario)
        self.db.commit()
        return self.get(user_id, scenario.id)

    def list_for_user(self, user_id: int) -> list[SimulationScenario]:
        return list(
            self.db.execute(
                select(SimulationScenario)
                .where(SimulationScenario.user_id == user_id)
                .order_by(desc(SimulationScenario.updated_at))
            ).scalars()
        )

    def get(self, user_id: int, scenario_id: int) -> SimulationScenario:
        """Чужий і відсутній сценарій однаково повертають 404, не розкриваючи дані."""
        scenario = self.db.execute(
            select(SimulationScenario)
            .options(selectinload(SimulationScenario.revisions))
            .where(SimulationScenario.id == scenario_id, SimulationScenario.user_id == user_id)
        ).scalar_one_or_none()
        if scenario is None:
            raise AppError("Сценарій не знайдено", status_code=404)
        return scenario

    def add_revision(
        self,
        user_id: int,
        scenario_id: int,
        payload: SimulationRevisionCreateRequest,
    ) -> SimulationScenario:
        # Блокування серіалізує нумерацію ревізій у PostgreSQL при паралельних запитах.
        scenario = self.db.execute(
            select(SimulationScenario)
            .where(SimulationScenario.id == scenario_id, SimulationScenario.user_id == user_id)
            .with_for_update()
        ).scalar_one_or_none()
        if scenario is None:
            raise AppError("Сценарій не знайдено", status_code=404)

        resolved_assumptions, source_refs = self._resolve_tuition(
            payload.assumptions,
            payload.tuition_snapshot_id,
            payload.tuition_snapshot_selection,
        )
        next_revision = scenario.current_revision_number + 1
        self.db.add(
            SimulationRevision(
                scenario_id=scenario.id,
                revision_number=next_revision,
                assumptions=resolved_assumptions.model_dump(mode="json"),
                methodology_version="scenario-foundation-v2",
                source_snapshot_refs=source_refs,
                change_note=payload.change_note,
            )
        )
        scenario.current_revision_number = next_revision
        scenario.target_role = resolved_assumptions.career_target
        scenario.country = resolved_assumptions.country
        scenario.currency = resolved_assumptions.currency
        self.db.commit()
        return self.get(user_id, scenario.id)
