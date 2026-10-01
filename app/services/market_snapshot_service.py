from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import MarketSnapshot
from app.schemas import MarketSnapshotCreateRequest, MarketSnapshotQuery


class MarketSnapshotService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    @staticmethod
    def _fingerprint(payload: MarketSnapshotCreateRequest) -> str:
        normalized = payload.model_dump(mode="json")
        normalized["role"] = payload.role.strip().casefold()
        normalized["country"] = payload.country.strip().casefold()
        normalized["seniority"] = payload.seniority.strip().casefold()
        normalized["methodology_version"] = payload.methodology_version.strip()
        canonical = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def create(self, payload: MarketSnapshotCreateRequest) -> tuple[MarketSnapshot, bool]:
        fingerprint = self._fingerprint(payload)
        existing = self.db.execute(
            select(MarketSnapshot).where(MarketSnapshot.fingerprint == fingerprint)
        ).scalar_one_or_none()
        if existing is not None:
            return existing, False

        snapshot = MarketSnapshot(
            role=payload.role.strip(),
            country=payload.country.strip(),
            seniority=payload.seniority.strip(),
            snapshot_date=payload.snapshot_date,
            currency=payload.currency,
            salary_min=payload.salary_min,
            median_salary=payload.median_salary,
            salary_max=payload.salary_max,
            vacancy_count=payload.vacancy_count,
            demand_index=payload.demand_index,
            sources=[source.model_dump(mode="json") for source in payload.sources],
            acquired_at=payload.acquired_at,
            sample_size=payload.sample_size,
            confidence=payload.confidence,
            methodology_version=payload.methodology_version.strip(),
            validation_status="validated",
            fingerprint=fingerprint,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot, True

    def get_validated(self, snapshot_id: int) -> MarketSnapshot:
        snapshot = self.db.execute(
            select(MarketSnapshot).where(
                MarketSnapshot.id == snapshot_id,
                MarketSnapshot.validation_status == "validated",
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise AppError("Market snapshot не знайдено", status_code=404)
        return snapshot

    def resolve_validated(
        self,
        *,
        role: str,
        country: str,
        seniority: str,
        currency: str,
        as_of_date: date,
        max_age_days: int,
        minimum_confidence: str,
    ) -> MarketSnapshot:
        """Resolve one reproducible salary source using explicit quality constraints."""

        confidence_rank = {"low": 1, "medium": 2, "high": 3}
        minimum_rank = confidence_rank[minimum_confidence]
        allowed_confidence = [
            label for label, rank in confidence_rank.items() if rank >= minimum_rank
        ]
        cutoff_date = as_of_date - timedelta(days=max_age_days)
        confidence_order = case(
            (MarketSnapshot.confidence == "high", 3),
            (MarketSnapshot.confidence == "medium", 2),
            else_=1,
        )

        snapshot = self.db.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.validation_status == "validated",
                func.lower(MarketSnapshot.role) == role.strip().lower(),
                func.lower(MarketSnapshot.country) == country.strip().lower(),
                func.lower(MarketSnapshot.seniority) == seniority.strip().lower(),
                MarketSnapshot.currency == currency.upper(),
                MarketSnapshot.salary_basis == "gross_annual",
                MarketSnapshot.snapshot_date >= cutoff_date,
                MarketSnapshot.snapshot_date <= as_of_date,
                MarketSnapshot.confidence.in_(allowed_confidence),
            )
            .order_by(
                MarketSnapshot.snapshot_date.desc(),
                confidence_order.desc(),
                func.coalesce(MarketSnapshot.sample_size, 0).desc(),
                MarketSnapshot.created_at.desc(),
                MarketSnapshot.id.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()
        if snapshot is None:
            raise AppError(
                "Немає validated market snapshot, що відповідає сценарію та правилам якості",
                status_code=422,
            )
        return snapshot

    def list_validated(self, query: MarketSnapshotQuery) -> list[MarketSnapshot]:
        statement = select(MarketSnapshot).where(MarketSnapshot.validation_status == "validated")
        if query.role:
            statement = statement.where(MarketSnapshot.role.ilike(f"%{query.role.strip()}%"))
        if query.country:
            statement = statement.where(MarketSnapshot.country == query.country.strip())
        if query.seniority:
            statement = statement.where(MarketSnapshot.seniority == query.seniority.strip())
        if query.currency:
            statement = statement.where(MarketSnapshot.currency == query.currency)
        statement = statement.order_by(
            MarketSnapshot.snapshot_date.desc(), MarketSnapshot.created_at.desc()
        ).limit(query.limit)
        return list(self.db.execute(statement).scalars())
