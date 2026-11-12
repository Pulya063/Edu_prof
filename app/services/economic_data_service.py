"""Official macro data (CPI inflation, exchange rates) for the countries Fence models.

Sources need no API key: World Bank indicators, the National Bank of Ukraine and
Narodowy Bank Polski. Values are stored as fetched; derived defaults are plain arithmetic.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from statistics import median
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EconomicIndicator

logger = logging.getLogger(__name__)

WORLD_BANK_CPI_URL = "https://api.worldbank.org/v2/country/{iso2}/indicator/FP.CPI.TOTL.ZG"
NBU_RATE_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
NBP_RATE_URL = "https://api.nbp.pl/api/exchangerates/rates/a/{code}/{start}/{end}/"
WORLD_BANK_ADVANCED_UNEMPLOYMENT_URL = "https://api.worldbank.org/v2/country/{iso2}/indicator/SL.UEM.ADVN.ZS"
EUROSTAT_MIN_WAGE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/earn_mw_cur"

# Country metadata only: ISO code, local currency and which central bank publishes its rates.
COUNTRIES: dict[str, dict[str, str]] = {
    "Poland": {"iso2": "PL", "currency": "PLN", "central_bank": "nbp", "baseline": "minimum_wage"},
    "Ukraine": {"iso2": "UA", "currency": "UAH", "central_bank": "nbu", "baseline": "median_vacancy_wage"},
}
FX_QUOTES = ("EUR", "USD")
HISTORY_YEARS = 10
TIMEOUT = httpx.Timeout(15.0)


class EconomicDataError(RuntimeError):
    """A provider answered with something that cannot be stored as an official value."""


def supported_country(country: str) -> str | None:
    return next((name for name in COUNTRIES if name.casefold() == country.strip().casefold()), None)


class EconomicDataService:
    def __init__(self, db_session: Session, client: httpx.Client | None = None) -> None:
        self.db = db_session
        self.client = client

    def _get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        if self.client is not None:
            response = self.client.get(url, params=params)
        else:
            with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
                response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _upsert(self, country: str, indicator: str, period: date, value: Decimal, unit: str, source_name: str, source_url: str) -> None:
        row = self.db.execute(
            select(EconomicIndicator).where(
                EconomicIndicator.country == country,
                EconomicIndicator.indicator == indicator,
                EconomicIndicator.period == period,
                EconomicIndicator.unit == unit,
            )
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if row is None:
            self.db.add(EconomicIndicator(
                country=country, indicator=indicator, period=period, value=value, unit=unit,
                source_name=source_name, source_url=source_url, acquired_at=now,
            ))
        else:
            row.value, row.source_name, row.source_url, row.acquired_at = value, source_name, source_url, now

    def _fetch_inflation(self, country: str, iso2: str, today: date) -> int:
        url = WORLD_BANK_CPI_URL.format(iso2=iso2)
        data = self._get_json(url, {"format": "json", "date": f"{today.year - HISTORY_YEARS}:{today.year}", "per_page": 100})
        if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
            raise EconomicDataError(f"World Bank CPI response for {country} has no data rows")
        stored = 0
        for row in data[1]:
            if row.get("value") is None:
                continue
            year = int(row["date"])
            self._upsert(country, "cpi_inflation", date(year, 12, 31), Decimal(str(row["value"])), "percent",
                         "World Bank, Inflation, consumer prices (annual %)", f"https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations={iso2}")
            stored += 1
        return stored

    def _fetch_graduate_unemployment(self, country: str, iso2: str) -> int:
        data = self._get_json(WORLD_BANK_ADVANCED_UNEMPLOYMENT_URL.format(iso2=iso2), {"format": "json", "mrnev": 3, "per_page": 3})
        if not isinstance(data, list) or len(data) < 2 or not isinstance(data[1], list):
            return 0
        stored = 0
        for row in data[1]:
            if row.get("value") is None:
                continue
            self._upsert(country, "graduate_unemployment", date(int(row["date"]), 12, 31), Decimal(str(row["value"])), "percent",
                         "World Bank, Unemployment with advanced education (%)", "https://data.worldbank.org/indicator/SL.UEM.ADVN.ZS")
            stored += 1
        return stored

    def _nbu_rate(self, quote: str, on: date) -> Decimal | None:
        data = self._get_json(NBU_RATE_URL, {"valcode": quote, "date": on.strftime("%Y%m%d"), "json": ""})
        if isinstance(data, list) and data and data[0].get("rate") is not None:
            return Decimal(str(data[0]["rate"]))
        return None

    def _nbp_rate(self, quote: str, on: date) -> Decimal | None:
        # NBP publishes on business days only; a short window returns the first published rate.
        url = NBP_RATE_URL.format(code=quote.lower(), start=on.isoformat(), end=(on + timedelta(days=9)).isoformat())
        try:
            data = self._get_json(url, {"format": "json"})
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                return None
            raise
        rates = data.get("rates") if isinstance(data, dict) else None
        return Decimal(str(rates[0]["mid"])) if rates else None

    def _fetch_fx(self, country: str, meta: dict[str, str], today: date) -> int:
        bank = meta["central_bank"]
        reader = self._nbu_rate if bank == "nbu" else self._nbp_rate
        source_name = "National Bank of Ukraine official rate" if bank == "nbu" else "Narodowy Bank Polski, table A"
        source_url = "https://bank.gov.ua/en/markets/exchangerates" if bank == "nbu" else "https://api.nbp.pl/"
        checkpoints = [date(today.year - offset, 1, 2) for offset in range(HISTORY_YEARS, -1, -1)]
        checkpoints.append(today - timedelta(days=9) if bank == "nbp" else today)
        stored = 0
        for quote in FX_QUOTES:
            unit = f"{meta['currency']} per {quote}"
            for on in checkpoints:
                rate = reader(quote, on)
                if rate is None:
                    continue
                self._upsert(country, "fx_rate", on, rate, unit, source_name, source_url)
                stored += 1
        return stored

    def _fetch_minimum_wage(self, country: str, meta: dict[str, str]) -> int:
        """Statutory monthly minimum wage in national currency (Eurostat earn_mw_cur, bi-annual)."""
        data = self._get_json(EUROSTAT_MIN_WAGE_URL, {"geo": meta["iso2"], "currency": "NAC", "format": "JSON", "lang": "en"})
        periods = {index: label for label, index in data["dimension"]["time"]["category"]["index"].items()}
        stored = 0
        for key, value in data.get("value", {}).items():
            label = periods[int(key)]
            year, half = label.split("-S")
            self._upsert(country, "minimum_wage", date(int(year), 1 if half == "1" else 7, 1), Decimal(str(value)),
                         f"{meta['currency']} per month", "Eurostat, monthly minimum wages (earn_mw_cur)",
                         f"https://ec.europa.eu/eurostat/databrowser/view/earn_mw_cur/default/table?geo={meta['iso2']}")
            stored += 1
        return stored

    def _fetch_register_median(self, country: str, meta: dict[str, str], today: date) -> int:
        """Median monthly salary of all vacancies in the State Employment Service register."""
        from app.services.market_ingestion_service import MarketIngestionService

        sample = MarketIngestionService(self.db, client=self.client)._state_employment_service(r".")
        if not sample.monthly:
            return 0
        value = Decimal(str(median(sample.monthly))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        source = sample.sources[0]
        self._upsert(country, "median_vacancy_wage", today, value, f"{meta['currency']} per month",
                     f"{source['name']} (median of {len(sample.monthly)} vacancies)", source["url"])
        return 1

    def refresh(self, country: str, today: date | None = None) -> dict[str, int]:
        name = supported_country(country)
        if name is None:
            raise EconomicDataError(f"No official economic sources configured for {country}")
        meta = COUNTRIES[name]
        today = today or date.today()
        result = {"cpi_inflation": self._fetch_inflation(name, meta["iso2"], today), "fx_rate": self._fetch_fx(name, meta, today)}
        result["graduate_unemployment"] = self._fetch_graduate_unemployment(name, meta["iso2"])
        if meta["baseline"] == "minimum_wage":
            result["minimum_wage"] = self._fetch_minimum_wage(name, meta)
        else:
            result["median_vacancy_wage"] = self._fetch_register_median(name, meta, today)
        self.db.commit()
        return result

    def _rows(self, country: str, indicator: str) -> list[EconomicIndicator]:
        return list(self.db.execute(
            select(EconomicIndicator)
            .where(EconomicIndicator.country == country, EconomicIndicator.indicator == indicator)
            .order_by(EconomicIndicator.unit, EconomicIndicator.period)
        ).scalars())

    def profile(self, country: str) -> dict[str, Any]:
        name = supported_country(country) or country.strip()
        meta = COUNTRIES.get(name, {})
        inflation = self._rows(name, "cpi_inflation")
        fx = self._rows(name, "fx_rate")

        latest = inflation[-1] if inflation else None
        window = inflation[-5:]
        suggested = None
        if window:
            suggested = Decimal(str(median([row.value for row in window]))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        devaluation = None
        eur = [row for row in fx if row.unit.endswith("per EUR")]
        if len(eur) >= 2:
            last = eur[-1]
            base = next((row for row in eur if (last.period - row.period).days >= 365 * 5 - 10), eur[0])
            years = Decimal((last.period - base.period).days) / Decimal("365.25")
            if years > 0 and base.value > 0:
                ratio = float(last.value / base.value)
                devaluation = Decimal(str((ratio ** (1 / float(years)) - 1) * 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        baseline_rows = self._rows(name, meta.get("baseline", "")) if meta else []
        baseline = baseline_rows[-1] if baseline_rows else None
        unemployment_rows = self._rows(name, "graduate_unemployment")
        unemployment = unemployment_rows[-1] if unemployment_rows else None

        series = []
        for indicator, rows in (("cpi_inflation", inflation), ("fx_rate", fx), (meta.get("baseline", "baseline"), baseline_rows)):
            for unit in dict.fromkeys(row.unit for row in rows):
                points = [row for row in rows if row.unit == unit]
                series.append({
                    "indicator": indicator, "unit": unit,
                    "source_name": points[-1].source_name, "source_url": points[-1].source_url,
                    "acquired_at": points[-1].acquired_at,
                    "points": [{"period": row.period, "value": row.value} for row in points],
                })

        return {
            "country": name,
            "currency": meta.get("currency"),
            "latest_inflation_percent": latest.value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if latest else None,
            "latest_inflation_year": latest.period.year if latest else None,
            "suggested_inflation_percent": suggested,
            "inflation_window": f"{window[0].period.year}–{window[-1].period.year}" if window else None,
            "devaluation_vs_eur_percent": devaluation,
            # What someone earns without the degree: statutory minimum wage or the register median.
            "baseline_monthly_wage": baseline.value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if baseline else None,
            "baseline_wage_kind": meta.get("baseline") if baseline else None,
            "baseline_wage_period": baseline.period if baseline else None,
            "baseline_wage_source_name": baseline.source_name if baseline else None,
            "baseline_wage_source_url": baseline.source_url if baseline else None,
            "graduate_unemployment_percent": unemployment.value if unemployment else None,
            "graduate_unemployment_year": unemployment.period.year if unemployment else None,
            "series": series,
        }
