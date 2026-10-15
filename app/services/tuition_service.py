"""Database access for normalized tuition reference data."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TuitionSnapshot

def get_tuition_history(db_session: Session, country: str) -> list[dict[str, Any]]:
    """Return all stored yearly tuition records for a country from snapshots."""
    rows = db_session.execute(
        select(TuitionSnapshot)
        .where(
            func.lower(TuitionSnapshot.country) == country.strip().lower(),
            TuitionSnapshot.scope == "country_average",
            TuitionSnapshot.validation_status == "validated",
        )
        .order_by(TuitionSnapshot.academic_year)
    ).scalars().all()

    return [
        {
            "year": row.academic_year,
            "tuition_in_state": float(row.annual_tuition_min),
            "tuition_out_of_state": float(row.annual_tuition_max),
            "avg_net_price": float(row.annual_tuition),
            "currency": row.currency,
            "source": row.sources[0].get('name', 'Admin') if row.sources else 'Admin',
            "source_url": row.sources[0].get('url') if row.sources else None,
        }
        for row in rows
    ]

def get_latest_tuition(db_session: Session, country: str) -> Decimal | None:
    """Return the latest in-state price from snapshots."""
    row = db_session.execute(
        select(TuitionSnapshot)
        .where(
            func.lower(TuitionSnapshot.country) == country.strip().lower(),
            TuitionSnapshot.scope == "country_average",
            TuitionSnapshot.validation_status == "validated",
        )
        .order_by(TuitionSnapshot.academic_year.desc())
    ).scalars().first()

    if row is None:
        return None
    return row.annual_tuition
