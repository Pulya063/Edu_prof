"""Official exchange rates for showing amounts in the currency a person chose.

One source, the National Bank of Poland table A (mid rates, PLN per unit), which also lists UAH, so every
pair converts through PLN. Calculations keep their own currency; only the display changes.
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)

NBP_TABLE_URL = "https://api.nbp.pl/api/exchangerates/tables/a/?format=json"
SUPPORTED = ("USD", "EUR", "GBP", "UAH")
CACHE_FOR = timedelta(hours=6)

_lock = threading.Lock()
_cache: dict | None = None


def convert(amount: Decimal, source: str, target: str, pln_per_unit: dict[str, Decimal]) -> Decimal | None:
    """amount in source currency -> target currency; None when a rate is missing."""
    rates = {**pln_per_unit, "PLN": Decimal("1")}
    if source not in rates or target not in rates:
        return None
    return amount * rates[source] / rates[target]


def latest_rates(client: httpx.Client | None = None) -> dict:
    """{"base": "PLN", "pln_per_unit": {...}, "effective_date", "source_name", "source_url"}; cached for six hours."""
    global _cache
    with _lock:
        if _cache and datetime.now(UTC) - _cache["fetched_at"] < CACHE_FOR:
            return _cache["data"]
    try:
        response = (client or httpx).get(NBP_TABLE_URL, timeout=15, headers={"Accept": "application/json"})
        response.raise_for_status()
        table = response.json()[0]
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as error:
        logger.warning("NBP exchange rates unavailable: %s", error)
        if _cache:
            return _cache["data"]
        raise
    pln_per_unit = {item["code"]: str(Decimal(str(item["mid"]))) for item in table["rates"] if item["code"] in SUPPORTED}
    data = {
        "base": "PLN", "pln_per_unit": pln_per_unit, "effective_date": table.get("effectiveDate"),
        "source_name": f"National Bank of Poland, table A {table.get('no', '')}".strip(), "source_url": "https://api.nbp.pl/",
    }
    with _lock:
        _cache = {"fetched_at": datetime.now(UTC), "data": data}
    return data
