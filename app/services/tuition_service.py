"""Database access for normalized tuition reference data."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TuitionPrice


def get_tuition_history(db_session: Session, country: str) -> list[dict[str, Any]]:
    """Return all stored yearly tuition records for a country."""
    rows = db_session.execute(
        select(TuitionPrice)
        .where(func.lower(TuitionPrice.country) == country.strip().lower())
        .order_by(TuitionPrice.academic_year)
    ).scalars().all()

    return [
        {
            "year": row.academic_year,
            "tuition_in_state": _as_float(row.tuition_in_state),
            "tuition_out_of_state": _as_float(row.tuition_out_of_state),
            "avg_net_price": _as_float(row.tuition_in_state),
            "currency": row.currency,
            "source": row.source,
            "source_url": row.source_url,
        }
        for row in rows
    ]


def get_latest_tuition(db_session: Session, country: str) -> Decimal | None:
    """Return the latest in-state price, or out-of-state price if needed."""
    row = db_session.execute(
        select(TuitionPrice)
        .where(func.lower(TuitionPrice.country) == country.strip().lower())
        .order_by(TuitionPrice.academic_year.desc())
    ).scalars().first()
    if row is None:
        return None
    return row.tuition_in_state or row.tuition_out_of_state


def _as_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None
