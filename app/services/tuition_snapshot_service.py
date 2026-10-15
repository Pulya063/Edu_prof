from __future__ import annotations

import hashlib
import json
from datetime import timedelta

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import TuitionSnapshot
from app.schemas import (
    TuitionSnapshotCreateRequest,
    TuitionSnapshotQuery,
    TuitionSnapshotSelection,
)


class TuitionSnapshotService:
    """Store and resolve reproducible tuition inputs without live request-time APIs."""

    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    @staticmethod
    def _fingerprint(payload: TuitionSnapshotCreateRequest) -> str:
        normalized = payload.model_dump(mode="json")
        # Fetch time is provenance, not identity. Re-fetching the same source
        # observation must not create a duplicate immutable snapshot.
        normalized.pop("acquired_at", None)
        for source in normalized.get("sources", []):
            source.pop("acquired_at", None)
        for field in ("country", "university", "program", "degree", "study_mode"):
            value = normalized.get(field)
            normalized[field] = value.strip().casefold() if value else None
        normalized["academic_year"] = payload.academic_year.strip()
        normalized["methodology_version"] = payload.methodology_version.strip()
        canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_snapshot(
        payload: TuitionSnapshotCreateRequest,
        fingerprint: str,
    ) -> TuitionSnapshot:
        return TuitionSnapshot(
            scope=payload.scope,
            country=payload.country.strip(),
            university=payload.university.strip() if payload.university else None,
            program=payload.program.strip() if payload.program else None,
            degree=payload.degree.strip() if payload.degree else None,
            study_mode=payload.study_mode.strip() if payload.study_mode else None,
            student_residency=payload.student_residency,
            institution_type=payload.institution_type,
            academic_year=payload.academic_year.strip(),
            snapshot_date=payload.snapshot_date,
            currency=payload.currency,
            annual_tuition_min=payload.annual_tuition_min,
            annual_tuition=payload.annual_tuition,
            annual_tuition_max=payload.annual_tuition_max,
            mandatory_fees=payload.mandatory_fees,
            sources=[source.model_dump(mode="json") for source in payload.sources],
            acquired_at=payload.acquired_at,
            confidence=payload.confidence,
            methodology_version=payload.methodology_version.strip(),
            validation_status="validated",
            fingerprint=fingerprint,
        )

    def create_many(
        self,
        payloads: list[TuitionSnapshotCreateRequest],
    ) -> list[tuple[TuitionSnapshot, bool]]:
        """Insert a provider batch atomically and deduplicate observations."""
        results: list[tuple[TuitionSnapshot, bool]] = []
        new_snapshots: list[TuitionSnapshot] = []

        for payload in payloads:
            fingerprint = self._fingerprint(payload)
            existing = self.db.execute(
                select(TuitionSnapshot).where(TuitionSnapshot.fingerprint == fingerprint)
            ).scalar_one_or_none()
            if existing is not None:
                results.append((existing, False))
                continue

            snapshot = self._build_snapshot(payload, fingerprint)
            self.db.add(snapshot)
            new_snapshots.append(snapshot)
            results.append((snapshot, True))

        self.db.commit()
        for snapshot in new_snapshots:
            self.db.refresh(snapshot)
        return results

    def create(self, payload: TuitionSnapshotCreateRequest) -> tuple[TuitionSnapshot, bool]:
        return self.create_many([payload])[0]

    def get_validated(self, snapshot_id: int) -> TuitionSnapshot:
        snapshot = self.db.execute(
            select(TuitionSnapshot).where(
                TuitionSnapshot.id == snapshot_id,
                TuitionSnapshot.validation_status == "validated",
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise AppError("Tuition snapshot не знайдено", status_code=404)
        return snapshot

    def resolve_validated(self, selection: TuitionSnapshotSelection) -> TuitionSnapshot:
        confidence_rank = {"low": 1, "medium": 2, "high": 3}
        minimum_rank = confidence_rank[selection.minimum_confidence]
        allowed_confidence = [
            label for label, rank in confidence_rank.items() if rank >= minimum_rank
        ]
        cutoff_date = selection.as_of_date - timedelta(days=selection.max_age_days)

        program_match = and_(
            TuitionSnapshot.scope == "program",
            func.lower(TuitionSnapshot.university) == selection.university.strip().lower(),
            func.lower(TuitionSnapshot.program) == selection.program.strip().lower(),
        )
        university_match = and_(
            TuitionSnapshot.scope == "university",
            func.lower(TuitionSnapshot.university) == selection.university.strip().lower(),
        )
        allowed_scopes = [program_match, university_match]
        if selection.allow_country_fallback:
            allowed_scopes.append(TuitionSnapshot.scope == "country_average")

        filters = [
            TuitionSnapshot.validation_status == "validated",
            func.lower(TuitionSnapshot.country) == selection.country.strip().lower(),
            TuitionSnapshot.currency == selection.currency,
            TuitionSnapshot.student_residency == selection.student_residency,
            TuitionSnapshot.snapshot_date >= cutoff_date,
            TuitionSnapshot.snapshot_date <= selection.as_of_date,
            TuitionSnapshot.confidence.in_(allowed_confidence),
            or_(*allowed_scopes),
        ]
        if selection.degree:
            filters.append(
                or_(
                    TuitionSnapshot.degree.is_(None),
                    func.lower(TuitionSnapshot.degree) == selection.degree.strip().lower(),
                )
            )
        if selection.study_mode:
            filters.append(
                or_(
                    TuitionSnapshot.study_mode.is_(None),
                    func.lower(TuitionSnapshot.study_mode) == selection.study_mode.strip().lower(),
                )
            )
        if selection.institution_type:
            filters.append(
                or_(
                    TuitionSnapshot.institution_type.is_(None),
                    TuitionSnapshot.institution_type == selection.institution_type,
                )
            )

        scope_order = case(
            (program_match, 3),
            (university_match, 2),
            else_=1,
        )
        confidence_order = case(
            (TuitionSnapshot.confidence == "high", 3),
            (TuitionSnapshot.confidence == "medium", 2),
            else_=1,
        )
        degree_order = case(
            (
                func.lower(TuitionSnapshot.degree)
                == (selection.degree or "").strip().lower(),
                1,
            ),
            else_=0,
        )

        snapshot = self.db.execute(
            select(TuitionSnapshot)
            .where(*filters)
            .order_by(
                scope_order.desc(),
                degree_order.desc(),
                TuitionSnapshot.snapshot_date.desc(),
                confidence_order.desc(),
                TuitionSnapshot.created_at.desc(),
                TuitionSnapshot.id.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()
        if snapshot is None:
            raise AppError(
                "Немає validated tuition snapshot, що відповідає програмі та правилам якості",
                status_code=422,
            )
        return snapshot

    def list_validated(self, query: TuitionSnapshotQuery) -> list[TuitionSnapshot]:
        statement = select(TuitionSnapshot).where(
            TuitionSnapshot.validation_status == "validated"
        )
        if query.country:
            statement = statement.where(
                func.lower(TuitionSnapshot.country) == query.country.strip().lower()
            )
        if query.university:
            statement = statement.where(
                TuitionSnapshot.university.ilike(f"%{query.university.strip()}%")
            )
        if query.program:
            statement = statement.where(
                TuitionSnapshot.program.ilike(f"%{query.program.strip()}%")
            )
        if query.degree:
            statement = statement.where(
                TuitionSnapshot.degree.ilike(f"%{query.degree.strip()}%")
            )
        if query.scope:
            statement = statement.where(TuitionSnapshot.scope == query.scope)
        if query.currency:
            statement = statement.where(TuitionSnapshot.currency == query.currency)
        statement = statement.order_by(
            TuitionSnapshot.snapshot_date.desc(),
            TuitionSnapshot.created_at.desc(),
        ).limit(query.limit)
        return list(self.db.execute(statement).scalars())
