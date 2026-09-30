from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError
from app.models import SimulationRevision, SimulationScenario
from app.schemas import SimulationCreateRequest, SimulationRevisionCreateRequest


class SimulationService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def create(self, user_id: int, payload: SimulationCreateRequest) -> SimulationScenario:
        assumptions = payload.assumptions.model_dump(mode="json")
        scenario = SimulationScenario(
            user_id=user_id,
            name=payload.name,
            target_role=payload.assumptions.career_target,
            country=payload.assumptions.country,
            currency=payload.assumptions.currency,
        )
        scenario.revisions.append(
            SimulationRevision(revision_number=1, assumptions=assumptions, source_snapshot_refs=[])
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
        scenario = self.db.execute(
            select(SimulationScenario)
            .where(SimulationScenario.id == scenario_id, SimulationScenario.user_id == user_id)
            .with_for_update()
        ).scalar_one_or_none()
        if scenario is None:
            raise AppError("Сценарій не знайдено", status_code=404)

        next_revision = scenario.current_revision_number + 1
        self.db.add(
            SimulationRevision(
                scenario_id=scenario.id,
                revision_number=next_revision,
                assumptions=payload.assumptions.model_dump(mode="json"),
                source_snapshot_refs=[],
                change_note=payload.change_note,
            )
        )
        scenario.current_revision_number = next_revision
        scenario.target_role = payload.assumptions.career_target
        scenario.country = payload.assumptions.country
        scenario.currency = payload.assumptions.currency
        self.db.commit()
        return self.get(user_id, scenario.id)
