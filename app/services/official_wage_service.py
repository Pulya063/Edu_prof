"""Official-statistics salary estimate, used when job listings have too few observations.

Poland only: Eurostat Structure of Earnings Survey 2022 (October 2022, enterprises of all sizes).

    sector mean   = mean monthly gross earnings of the occupation group in the economic sector (earn_ses22_48)
    junior ratio  = mean monthly earnings of that group aged under 30 / all ages (earn_ses22_21)
    CPI factor    = product of (1 + annual CPI inflation) for every year after 2022 (World Bank, stored)
    estimate      = sector mean × junior ratio × CPI factor × 12

Every input is an official published figure and the arithmetic is deterministic. The survey reports a
mean, not a range, so the snapshot's minimum, median and maximum are the same value and the result is
marked "medium" confidence: a large official sample, but an occupation group rather than one job title.
Ukraine has no comparable occupation table; its official source is the State Employment Service
vacancy register, which MarketIngestionService already uses directly.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EconomicIndicator, MarketSnapshot
from app.schemas import MarketSnapshotCreateRequest
from app.services.market_ingestion_service import ROLE_CATALOG, SENIORITY, MarketIngestionService, MarketProviderError
from app.services.market_snapshot_service import MarketSnapshotService

logger = logging.getLogger(__name__)

EUROSTAT_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}"
EUROSTAT_VIEW = "https://ec.europa.eu/eurostat/databrowser/view/{dataset}/default/table"
SES_YEAR = 2022
METHODOLOGY_VERSION = "eurostat-ses2022-occupation-sector-v1"
ISCO_LABEL = {"OC2": "professionals", "OC3": "technicians and associate professionals"}
OFFICIAL_COUNTRIES = {"Poland": {"geo": "PL", "currency": "PLN"}}
# A listing-based snapshot this recent is kept; the official estimate only fills gaps.
LISTING_PRIORITY_DAYS = 180


class OfficialWageError(RuntimeError):
    """An official figure needed for the estimate is missing."""


class OfficialWageService:
    def __init__(self, db_session: Session, client: httpx.Client | None = None) -> None:
        self.db = db_session
        self.client = client

    def _eurostat_value(self, dataset: str, **filters: str) -> float:
        params = {"format": "JSON", "lang": "en", **filters}
        if self.client is not None:
            response = self.client.get(EUROSTAT_URL.format(dataset=dataset), params=params)
        else:
            with httpx.Client(timeout=httpx.Timeout(60.0), follow_redirects=True) as client:
                response = client.get(EUROSTAT_URL.format(dataset=dataset), params=params)
        response.raise_for_status()
        data = response.json()
        # numpy and pandas load here, not at import, to keep them out of the API process until needed.
        import numpy as np
        import pandas as pd

        # Every dimension is filtered to one category, so the cube has exactly one cell.
        values = pd.Series(data.get("value") or {}, dtype="float64")
        if len(values) != 1 or not np.isfinite(values.iloc[0]):
            raise OfficialWageError(f"{dataset} has no single value for {filters}")
        return float(values.iloc[0])

    def cpi_factor(self, country: str) -> tuple[float, list[int]]:
        """Cumulative price change since the survey year, from stored annual CPI inflation."""
        import numpy as np
        import pandas as pd

        rows = self.db.execute(
            select(EconomicIndicator.period, EconomicIndicator.value)
            .where(EconomicIndicator.country == country, EconomicIndicator.indicator == "cpi_inflation")
        ).all()
        frame = pd.DataFrame(rows, columns=["period", "value"])
        if frame.empty:
            raise OfficialWageError(f"No CPI inflation stored for {country}; run the economics refresh first")
        frame["year"] = pd.to_datetime(frame["period"]).dt.year
        frame["value"] = frame["value"].astype("float64")
        by_year = frame.drop_duplicates("year", keep="last").set_index("year")["value"].sort_index()
        after = by_year[by_year.index > SES_YEAR]
        factor = float(np.prod(1 + after.to_numpy() / 100)) if len(after) else 1.0
        return factor, [int(year) for year in after.index]

    def estimate(self, role: str, country: str, today: date | None = None) -> MarketSnapshotCreateRequest:
        meta = OFFICIAL_COUNTRIES.get(country.strip().title())
        spec = next((value for name, value in ROLE_CATALOG.items() if name.casefold() == role.strip().casefold()), None)
        if meta is None or spec is None or "ses" not in spec:
            raise OfficialWageError(f"No official occupation statistics for {role} in {country}")
        canonical_role = next(name for name in ROLE_CATALOG if name.casefold() == role.strip().casefold())
        isco, nace = spec["ses"]
        common = {"geo": meta["geo"], "sex": "T", "unit": "NAC", "isco08": isco, "indic_se": "ERN", "sizeclas": "TOTAL"}

        sector_mean = self._eurostat_value("earn_ses22_48", nace_r2=nace, **common)
        under_30 = self._eurostat_value("earn_ses22_21", age="Y_LT30", **common)
        all_ages = self._eurostat_value("earn_ses22_21", age="TOTAL", **common)
        factor, years = self.cpi_factor(country.strip().title())

        monthly = sector_mean * (under_30 / all_ages) * factor
        annual = (Decimal(str(round(float(monthly), 6))) * 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        now = datetime.now(UTC)
        stamp = now.isoformat()
        group = ISCO_LABEL.get(isco, isco)
        cpi_note = f"CPI {years[0]}–{years[-1]} ×{factor:.4f}" if years else "no CPI change after 2022 stored"
        sources = [
            {"name": f"Eurostat SES {SES_YEAR}: mean monthly earnings of {group} in NACE {nace} ({sector_mean:,.0f} {meta['currency']})",
             "reference": f"eurostat:earn_ses22_48:{meta['geo']}:{isco}:{nace}", "url": EUROSTAT_VIEW.format(dataset="earn_ses22_48"), "acquired_at": stamp},
            {"name": f"Eurostat SES {SES_YEAR}: {group} under 30 earn {under_30 / all_ages:.3f} of the all-age mean",
             "reference": f"eurostat:earn_ses22_21:{meta['geo']}:{isco}:Y_LT30/TOTAL", "url": EUROSTAT_VIEW.format(dataset="earn_ses22_21"), "acquired_at": stamp},
            {"name": f"World Bank CPI inflation, {cpi_note}, brings October {SES_YEAR} pay to today's prices",
             "reference": f"economic_indicators:cpi_inflation:{country.strip().title()}", "url": "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG", "acquired_at": stamp},
        ]
        return MarketSnapshotCreateRequest(
            role=canonical_role, country=country.strip().title(), seniority=SENIORITY, snapshot_date=today or now.date(),
            currency=meta["currency"], salary_min=annual, median_salary=annual, salary_max=annual,
            vacancy_count=None, sources=sources, acquired_at=now, sample_size=None, confidence="medium",
            methodology_version=METHODOLOGY_VERSION,
        )

    def has_recent_listing_snapshot(self, role: str, country: str, today: date | None = None) -> bool:
        cutoff = (today or date.today()) - timedelta(days=LISTING_PRIORITY_DAYS)
        return self.db.execute(
            select(MarketSnapshot.id).where(
                MarketSnapshot.role == role, MarketSnapshot.country == country,
                MarketSnapshot.validation_status == "validated", MarketSnapshot.snapshot_date >= cutoff,
                MarketSnapshot.methodology_version != METHODOLOGY_VERSION,
            ).limit(1)
        ).first() is not None


def refresh_salary_snapshot(db_session: Session, role: str, country: str, currency: str | None = None,
                            ingestion: MarketIngestionService | None = None) -> tuple[MarketSnapshot, bool, str] | None:
    """Listings first; for Poland the official estimate fills in when listings are too thin.

    Returns (snapshot, created, "listings" | "official") or None when the role has no source here.
    """
    ingestion = ingestion or MarketIngestionService(db_session)
    listing_error: Exception | None = None
    listing: tuple[MarketSnapshot, bool] | None = None
    try:
        listing = ingestion.fetch_live(role, country, currency)
    except (MarketProviderError, httpx.HTTPError) as error:
        logger.info("Listings unavailable for %s in %s: %s", role, country, error)
        listing_error = error

    name = country.strip().title()
    # Listings with a solid sample are the answer. A thin (low-confidence) sample is kept, and for
    # Poland the official estimate is added beside it, because calculations require medium confidence.
    if listing is not None and listing[0].confidence != "low":
        return (*listing, "listings")
    if name not in OFFICIAL_COUNTRIES:
        if listing is not None:
            return (*listing, "listings")
        if listing_error is not None:
            raise listing_error
        return None
    official = OfficialWageService(db_session)
    canonical = next((item for item in ROLE_CATALOG if item.casefold() == role.strip().casefold()), role)
    if listing is None and official.has_recent_listing_snapshot(canonical, name):
        if listing_error is not None:
            raise listing_error
        return None
    snapshot, created = MarketSnapshotService(db_session).create(official.estimate(role, country))
    return snapshot, created, "official"
