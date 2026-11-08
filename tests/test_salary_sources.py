from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from app.models import EconomicIndicator, MarketSnapshot
from app.services.market_ingestion_service import (
    ALL_LEVELS,
    ROLE_CATALOG,
    SUPPORTED_ROLES,
    MarketIngestionService,
    MarketProviderError,
    SalarySample,
)
from app.services.official_wage_service import METHODOLOGY_VERSION, OfficialWageService, refresh_salary_snapshot

SOURCE = [{"name": "Test", "reference": "test:1", "url": "https://example.org"}]


def _sample(values):
    return SalarySample(monthly=[Decimal(str(v)) for v in values], sources=SOURCE, vacancy_count=len(values))


def test_catalogue_covers_fourteen_roles_in_both_countries():
    assert len(SUPPORTED_ROLES) == 14
    providers = MarketIngestionService(None).providers()
    assert len(providers) == 28
    assert all("ses" in spec for spec in ROLE_CATALOG.values())


def test_far_out_typo_is_dropped_but_ordinary_spread_kept():
    # Nine monthly salaries and one annual figure typed into the monthly field.
    values = [6000, 6500, 7000, 7200, 7500, 8000, 8200, 9000, 9500, 96000]
    cleaned = MarketIngestionService.clean_observations([Decimal(v) for v in values])
    assert 96000 not in cleaned and len(cleaned) == 9
    payload = MarketIngestionService.build_payload("Nurse", "Poland", "PLN", _sample(values))
    assert payload.sample_size == 9
    assert payload.median_salary == Decimal(str(np.median(values[:-1]) * 12)).quantize(Decimal("0.01"))


def test_small_samples_are_not_trimmed():
    cleaned = MarketIngestionService.clean_observations([Decimal(v) for v in (3000, 4000, 5000, 6000, 60000)])
    assert len(cleaned) == 5


def test_collect_falls_back_to_all_levels_when_juniors_are_too_few(monkeypatch):
    service = MarketIngestionService(None)
    calls = []

    def fake_source(source):
        calls.append(source[0])
        return _sample([5000, 5200]) if source[0] == "pracuj" else _sample([7000, 7500, 8000, 8500, 9000, 9500])

    monkeypatch.setattr(service, "_source", fake_source)
    currency, seniority, sample = service.collect("Nurse", "Poland")
    assert (currency, seniority, len(sample.monthly)) == ("PLN", ALL_LEVELS, 6)
    assert calls == ["pracuj", "pracuj_all"]


def test_collect_reports_every_tier_when_nothing_is_enough(monkeypatch):
    service = MarketIngestionService(None)
    monkeypatch.setattr(service, "_source", lambda source: _sample([5000]))
    with pytest.raises(MarketProviderError, match="junior: 1 observations; all levels: 1 observations"):
        service.collect("Teacher", "Poland")


def _seed_cpi(db_session, values):
    now = datetime.now(UTC)
    for year, value in values.items():
        db_session.add(EconomicIndicator(country="Poland", indicator="cpi_inflation", period=date(year, 12, 31), value=Decimal(str(value)),
                                         unit="percent", source_name="World Bank", source_url="https://data.worldbank.org", acquired_at=now))
    db_session.commit()


def _fake_eurostat(monkeypatch):
    cells = {("earn_ses22_48", "Q"): 8861.0, ("earn_ses22_21", "Y_LT30"): 7134.0, ("earn_ses22_21", "TOTAL"): 7997.0}
    seen = []

    def value(self, dataset, **filters):
        seen.append((dataset, filters))
        return cells[(dataset, filters.get("nace_r2") or filters.get("age"))]

    monkeypatch.setattr(OfficialWageService, "_eurostat_value", value)
    return seen


def test_official_estimate_is_sector_mean_times_junior_ratio_times_cpi(db_session, monkeypatch):
    _seed_cpi(db_session, {2021: 5.1, 2022: 14.4, 2023: 11.4, 2024: 3.7})
    seen = _fake_eurostat(monkeypatch)

    payload = OfficialWageService(db_session).estimate("nurse", "Poland")

    # 8 861 × (7 134 / 7 997) × 1.114 × 1.037 × 12; 2021 and 2022 are before or in the survey year.
    expected = Decimal(str(round(8861 * (7134 / 7997) * 1.114 * 1.037, 6))) * 12
    assert payload.median_salary == expected.quantize(Decimal("0.01"))
    assert payload.salary_min == payload.median_salary == payload.salary_max
    assert (payload.role, payload.seniority, payload.confidence) == ("Nurse", "junior", "medium")
    assert payload.methodology_version == METHODOLOGY_VERSION
    assert {filters["isco08"] for _, filters in seen} == {"OC2"} and len(payload.sources) == 3


def test_official_estimate_needs_stored_cpi(db_session, monkeypatch):
    _fake_eurostat(monkeypatch)
    with pytest.raises(Exception, match="No CPI inflation stored"):
        OfficialWageService(db_session).estimate("Nurse", "Poland")


def test_official_estimate_only_for_poland(db_session):
    with pytest.raises(Exception, match="No official occupation statistics"):
        OfficialWageService(db_session).estimate("Nurse", "Ukraine")


def _failing_ingestion(db_session, monkeypatch):
    ingestion = MarketIngestionService(db_session)
    monkeypatch.setattr(ingestion, "collect", lambda role, country: (_ for _ in ()).throw(MarketProviderError("too few")))
    return ingestion


def test_refresh_uses_official_estimate_when_listings_are_thin(db_session, monkeypatch):
    _seed_cpi(db_session, {2023: 11.4, 2024: 3.7})
    _fake_eurostat(monkeypatch)

    snapshot, created, origin = refresh_salary_snapshot(db_session, "Nurse", "Poland", "PLN", ingestion=_failing_ingestion(db_session, monkeypatch))

    assert (origin, created, snapshot.methodology_version) == ("official", True, METHODOLOGY_VERSION)


def test_refresh_keeps_a_recent_listing_snapshot(db_session, monkeypatch):
    _seed_cpi(db_session, {2023: 11.4})
    _fake_eurostat(monkeypatch)
    db_session.add(MarketSnapshot(
        role="Nurse", country="Poland", seniority=ALL_LEVELS, snapshot_date=date.today() - timedelta(days=20), currency="PLN",
        salary_basis="gross_annual", salary_min=Decimal("80000"), median_salary=Decimal("90000"), salary_max=Decimal("100000"),
        vacancy_count=22, sources=SOURCE, acquired_at=datetime.now(UTC), sample_size=22, confidence="medium",
        methodology_version="listing-quartiles-v2", validation_status="validated", fingerprint="n" * 64,
    ))
    db_session.commit()

    with pytest.raises(MarketProviderError):
        refresh_salary_snapshot(db_session, "Nurse", "Poland", "PLN", ingestion=_failing_ingestion(db_session, monkeypatch))
    assert db_session.query(MarketSnapshot).count() == 1


def test_ukraine_has_no_official_fallback(db_session, monkeypatch):
    with pytest.raises(MarketProviderError):
        refresh_salary_snapshot(db_session, "Nurse", "Ukraine", "UAH", ingestion=_failing_ingestion(db_session, monkeypatch))



def test_solid_broad_sample_beats_thin_junior_sample(monkeypatch):
    service = MarketIngestionService(None)
    monkeypatch.setattr(service, "_source", lambda source: _sample(range(5000, 5700, 100)) if source[0] == "pracuj" else _sample(range(6000, 9000, 100)))
    assert service.collect("Teacher", "Poland")[1] == ALL_LEVELS

    monkeypatch.setattr(service, "_source", lambda source: _sample(range(5000, 6200, 100)))
    assert service.collect("Teacher", "Poland")[1] == "junior"


def test_thin_listing_sample_in_poland_gets_the_official_estimate_beside_it(db_session, monkeypatch):
    _seed_cpi(db_session, {2023: 11.4})
    _fake_eurostat(monkeypatch)
    ingestion = MarketIngestionService(db_session)
    monkeypatch.setattr(ingestion, "collect", lambda role, country: ("PLN", "junior", _sample([7000, 7200, 7400, 7600, 7800, 8000, 8200])))

    snapshot, _created, origin = refresh_salary_snapshot(db_session, "Nurse", "Poland", "PLN", ingestion=ingestion)

    assert origin == "official" and snapshot.confidence == "medium"
    assert {row.methodology_version for row in db_session.query(MarketSnapshot)} == {"listing-quartiles-v2", METHODOLOGY_VERSION}
