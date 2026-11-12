"""How pay grows with experience after the first job, from career-level market data.

Deterministic and sourced: the median pay of junior, mid and senior listings (or survey answers) for the
same role, country and currency. Years 1-2 after graduating are junior, 3-5 mid, 6 and later senior, and
the pay then stays at the senior level. A level with no data ends the ladder there, so the pay simply stays
at the last known level; nothing is estimated. A level that pays less than the one before it (a sampling
artefact between different listings) keeps the previous level's pay.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MarketSnapshot
from app.schemas import ProjectionEvidence, SimulationProjectionRequest

logger = logging.getLogger(__name__)

LEVELS = ("junior", "mid", "senior")
# Years after graduating spent at each level before the next one.
YEARS_AT_LEVEL = {"junior": 2, "mid": 3}
MAX_AGE_DAYS = 365


def ladder_from_medians(start_level: str, start_pay: Decimal, medians: dict[str, Decimal], horizon_years: int) -> list[Decimal]:
    """Multiplier of the starting pay for each year after graduating; empty when no later level is known."""
    if start_level not in LEVELS or start_pay <= 0:
        return []
    order = LEVELS[LEVELS.index(start_level):]
    known: list[tuple[str, Decimal]] = [(start_level, Decimal("1"))]
    for level in order[1:]:
        median = medians.get(level)
        if median is None or median <= 0:
            break
        known.append((level, max(known[-1][1], (median / start_pay).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))))
    if len(known) == 1:
        return []
    ladder: list[Decimal] = []
    for level, multiplier in known:
        span = YEARS_AT_LEVEL.get(level, horizon_years) if level != known[-1][0] else horizon_years
        ladder.extend([multiplier] * span)
    return ladder[:horizon_years]


class CareerLadderService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def _latest(self, role: str, country: str, currency: str, level: str) -> MarketSnapshot | None:
        cutoff = date.today() - timedelta(days=MAX_AGE_DAYS)
        return self.db.execute(
            select(MarketSnapshot).where(
                MarketSnapshot.validation_status == "validated",
                func.lower(MarketSnapshot.role) == role.strip().lower(),
                func.lower(MarketSnapshot.country) == country.strip().lower(),
                func.lower(MarketSnapshot.seniority) == level,
                MarketSnapshot.currency == currency.upper(),
                MarketSnapshot.salary_basis == "gross_annual",
                MarketSnapshot.snapshot_date >= cutoff,
            ).order_by(MarketSnapshot.snapshot_date.desc(), MarketSnapshot.id.desc()).limit(1)
        ).scalar_one_or_none()

    def _fetch(self, role: str, country: str, currency: str, level: str) -> MarketSnapshot | None:
        """Read current listings at this level for a catalogue role; None when no source has enough."""
        from flask import current_app, has_app_context

        from app.services.market_ingestion_service import ROLE_CATALOG, MarketIngestionService, MarketProviderError

        # Tests never reach live job boards; stored snapshots are enough for them.
        if has_app_context() and current_app.config.get("TESTING"):
            return None
        if not any(name.casefold() == role.strip().casefold() for name in ROLE_CATALOG):
            return None
        try:
            return MarketIngestionService(self.db).fetch_level(role, country, level, currency)
        except (MarketProviderError, httpx.HTTPError, ValueError, KeyError) as error:
            logger.info("No %s salary data for %s in %s: %s", level, role, country, error)
            return None

    def attach(self, assumptions: dict, payload: SimulationProjectionRequest, fetch: bool) -> SimulationProjectionRequest:
        """The payload with its career ladder and one evidence record per later level used."""
        if payload.career_ladder is not None or payload.annual_start_salary is None:
            return payload
        start = next((item for item in payload.evidence if item.metric == "target_start_salary"), None)
        start_level = (start.seniority if start else "").strip().casefold()
        if start_level not in LEVELS:
            return payload
        role, country, currency = assumptions["career_target"], assumptions["country"], assumptions["currency"]
        stored = [item for item in payload.evidence if item.metric == "career_level"]
        snapshots: dict[str, MarketSnapshot] = {}
        if stored:
            # A recalculation reuses exactly the snapshots the saved forecast used.
            for item in stored:
                reference = item.source_reference.removeprefix("market_snapshot:")
                snapshot = self.db.get(MarketSnapshot, int(reference)) if reference.isdigit() else None
                if snapshot is not None:
                    snapshots[snapshot.seniority.casefold()] = snapshot
        else:
            for level in LEVELS[LEVELS.index(start_level) + 1:]:
                snapshot = self._latest(role, country, currency, level) or (self._fetch(role, country, currency, level) if fetch else None)
                if snapshot is None:
                    break
                snapshots[level] = snapshot

        # Ratios compare market medians with each other. A start salary from the market is that median;
        # a salary the person typed grows by the market's level-to-level ratios.
        if start is not None and start.source_reference.startswith("market_snapshot:"):
            start_pay = payload.annual_start_salary
        else:
            base = self._latest(role, country, currency, start_level)
            if base is None:
                return payload
            start_pay = base.median_salary
        ladder = ladder_from_medians(start_level, start_pay, {level: item.median_salary for level, item in snapshots.items()}, payload.horizon_years)
        if not ladder:
            return payload
        evidence = [item for item in payload.evidence if item.metric != "career_level"]
        used: list[str] = []
        for level in LEVELS[LEVELS.index(start_level) + 1:]:
            if level not in snapshots:
                break
            used.append(level)
        for level in used:
            snapshot = snapshots[level]
            evidence.append(ProjectionEvidence(
                metric="career_level", source_name=f"Fence market snapshot, {level} pay"[:255], source_reference=f"market_snapshot:{snapshot.id}",
                acquired_at=snapshot.acquired_at or datetime.now(UTC), country=snapshot.country, role=snapshot.role, seniority=level,
                currency=snapshot.currency, sample_size=snapshot.sample_size, confidence=snapshot.confidence,
            ))
        return payload.model_copy(update={"career_ladder": ladder, "evidence": evidence[:20]})
