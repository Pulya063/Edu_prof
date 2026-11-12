from decimal import Decimal
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models import TuitionSnapshot
from app.services.tuition_service import get_latest_tuition, get_tuition_history


def test_tuition_history_is_loaded_from_database(db_session: Session) -> None:
    db_session.add_all([
        TuitionSnapshot(
            scope="country_average",
            country="Ukraine",
            academic_year="2023",
            snapshot_date=date(2023, 9, 1),
            annual_tuition_min=Decimal("1700.00"),
            annual_tuition=Decimal("1700.00"),
            annual_tuition_max=Decimal("3400.00"),
            currency="USD",
            sources=[{"name": "test", "url": "https://example.test/2023"}],
            acquired_at=datetime(2023, 9, 1, tzinfo=timezone.utc),
            confidence="medium",
            methodology_version="test-v1",
            validation_status="validated",
            fingerprint="1" * 64,
        ),
        TuitionSnapshot(
            scope="country_average",
            country="Ukraine",
            academic_year="2024",
            snapshot_date=date(2024, 9, 1),
            annual_tuition_min=Decimal("1800.00"),
            annual_tuition=Decimal("1800.00"),
            annual_tuition_max=Decimal("3600.00"),
            currency="USD",
            sources=[{"name": "test", "url": "https://example.test/2024"}],
            acquired_at=datetime(2024, 9, 1, tzinfo=timezone.utc),
            confidence="medium",
            methodology_version="test-v1",
            validation_status="validated",
            fingerprint="2" * 64,
        ),
    ])
    db_session.commit()

    history = get_tuition_history(db_session, "ukraine")

    assert [row["year"] for row in history] == ["2023", "2024"]
    assert history[-1]["tuition_in_state"] == 1800.0
    assert get_latest_tuition(db_session, "UKRAINE") == Decimal("1800.00")
