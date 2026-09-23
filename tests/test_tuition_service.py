from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import TuitionPrice
from app.services.tuition_service import get_latest_tuition, get_tuition_history


def test_tuition_history_is_loaded_from_database(db_session: Session) -> None:
    db_session.add_all([
        TuitionPrice(
            country="Ukraine",
            academic_year=2023,
            tuition_in_state=Decimal("1700.00"),
            tuition_out_of_state=Decimal("3400.00"),
            currency="USD",
            source="test",
        ),
        TuitionPrice(
            country="Ukraine",
            academic_year=2024,
            tuition_in_state=Decimal("1800.00"),
            tuition_out_of_state=Decimal("3600.00"),
            currency="USD",
            source="test",
        ),
    ])
    db_session.commit()

    history = get_tuition_history(db_session, "ukraine")

    assert [row["year"] for row in history] == [2023, 2024]
    assert history[-1]["tuition_in_state"] == 1800.0
    assert get_latest_tuition(db_session, "UKRAINE") == Decimal("1800.00")
