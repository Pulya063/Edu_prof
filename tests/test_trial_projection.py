from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.models import EconomicIndicator, MarketSnapshot


def _seed_ukraine_python(db_session) -> None:
    """KNU Python reference: median 546 450 UAH, baseline 15 000 UAH a month, CPI 12.73 %."""
    now = datetime.now(UTC)
    db_session.add(MarketSnapshot(
        role="Python Backend Developer", country="Ukraine", seniority="junior", snapshot_date=date.today() - timedelta(days=3),
        currency="UAH", salary_basis="gross_annual", salary_min=Decimal("430603.00"), median_salary=Decimal("546450.00"),
        salary_max=Decimal("710385.00"), vacancy_count=40, sources=[{"name": "test", "reference": "test:1"}], acquired_at=now,
        sample_size=40, confidence="high", methodology_version="market-normalization-v1", validation_status="validated",
        fingerprint="a" * 64,
    ))
    common = {"country": "Ukraine", "source_name": "test", "source_url": "https://example.org", "acquired_at": now}
    for year in range(2021, 2026):
        db_session.add(EconomicIndicator(indicator="cpi_inflation", period=date(year, 12, 31), value=Decimal("12.73"), unit="percent", **common))
    db_session.add(EconomicIndicator(indicator="median_vacancy_wage", period=date(2026, 11, 4), value=Decimal("15000"), unit="UAH per month", **common))
    db_session.commit()


def test_trial_preview_matches_hand_calculated_reference(client, db_session):
    _seed_ukraine_python(db_session)
    response = client.post("/api/roi/preview", json={
        "country": "Ukraine", "career_target": "python backend developer", "university": "KNU",
        "study_years": 4, "annual_tuition": 0, "job_search_months": 3, "target_payback_years": 3,
    })

    assert response.status_code == 200, response.get_json()
    body = response.get_json()
    # Investment = 4 years × 180 000 UAH of baseline income given up, no tuition.
    assert body["total_investment"] == 720000.0
    assert body["currency"] == "UAH" and body["career_target"] == "Python Backend Developer"
    # Year 1: 546 450 × 9/12 − 180 000 = 229 837.5; then 366 450 a year -> 12 + ceil(16.05) = 29 months.
    assert body["payback_months"] == 29
    assert body["payback_from_enrollment_months"] == 48 + 29
    assert body["payback_within_target"] is True
    assert [item["scenario"] for item in body["scenarios"]] == ["pessimistic", "base", "optimistic"]
    assert len(body["trajectory"]) == 10
    assert {item["metric"] for item in body["sources"]} == {"target_start_salary", "baseline_salary", "inflation"}
    assert body["sources"][0]["source_name"] == "test"


def test_trial_preview_saves_nothing(client, db_session):
    from app.models import SimulationProjection

    _seed_ukraine_python(db_session)
    client.post("/api/roi/preview", json={"country": "Ukraine", "career_target": "Python Backend Developer"})

    assert db_session.query(SimulationProjection).count() == 0


def test_trial_preview_reports_missing_data_instead_of_guessing(client, db_session):
    response = client.post("/api/roi/preview", json={"country": "Poland", "career_target": "Lawyer"})

    assert response.status_code == 422


def test_trial_preview_rejects_unknown_country(client):
    response = client.post("/api/roi/preview", json={"country": "Germany", "career_target": "Lawyer"})

    assert response.status_code == 422


def test_trial_options_list_only_roles_with_data(client, db_session):
    _seed_ukraine_python(db_session)

    options = client.get("/api/roi/preview/options").get_json()

    assert options == [{"country": "Ukraine", "currency": "UAH", "career_target": "Python Backend Developer", "median_salary": 546450.0,
                        "seniority": "junior", "salary_source": "listings"}]


def test_showcase_contains_only_cases_with_data_and_can_be_cached(client, db_session):
    _seed_ukraine_python(db_session)

    response = client.get("/api/roi/preview/showcase")

    assert response.status_code == 200 and "max-age=600" in response.headers["Cache-Control"]
    body = response.get_json()
    assert [item["key"] for item in body["scenarios"]] == ["knu-python"]
    assert body["scenarios"][0]["result"]["payback_months"] == 29
    assert body["grant_example"] is None and len(body["careers"]) == 1


def test_showcase_grant_lowers_investment_by_the_grant(client, db_session):
    now = datetime.now(UTC)
    db_session.add(MarketSnapshot(
        role="Python Backend Developer", country="Poland", seniority="junior", snapshot_date=date.today(), currency="PLN",
        salary_basis="gross_annual", salary_min=Decimal("104400"), median_salary=Decimal("114000"), salary_max=Decimal("146340"), vacancy_count=11,
        sources=[{"name": "test", "reference": "test:1"}], acquired_at=now, sample_size=11, confidence="medium",
        methodology_version="listing-quartiles-v2", validation_status="validated", fingerprint="b" * 64,
    ))
    common = {"country": "Poland", "source_name": "test", "source_url": "https://example.org", "acquired_at": now}
    for year in range(2021, 2026):
        db_session.add(EconomicIndicator(indicator="cpi_inflation", period=date(year, 12, 31), value=Decimal("5.06"), unit="percent", **common))
    db_session.add(EconomicIndicator(indicator="minimum_wage", period=date(2026, 7, 1), value=Decimal("4806"), unit="PLN per month", **common))
    db_session.commit()

    example = client.get("/api/roi/preview/showcase").get_json()["grant_example"]

    assert example["without_grant"]["total_investment"] - example["with_grant"]["total_investment"] == 30000.0
    assert example["with_grant"]["payback_months"] < example["without_grant"]["payback_months"]
