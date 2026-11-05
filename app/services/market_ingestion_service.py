"""Live salary collection for the roles Fence supports, turned into validated market snapshots.

Every number comes from a public listing or survey and is reduced with plain statistics
(quartiles of monthly midpoints × 12). No source is invented or estimated by a model.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from statistics import median, quantiles
from xml.etree import ElementTree

import httpx
from sqlalchemy.orm import Session

from app.models import MarketSnapshot
from app.schemas import MarketSnapshotCreateRequest
from app.services.market_snapshot_service import ALL_LEVELS, MarketSnapshotService

logger = logging.getLogger(__name__)

METHODOLOGY_VERSION = "listing-quartiles-v1"
SENIORITY = "junior"
MIN_SAMPLE = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
TIMEOUT = httpx.Timeout(40.0)

NOFLUFF_SEARCH_URL = "https://nofluffjobs.com/api/search/posting"
PRACUJ_URL = "https://www.pracuj.pl/praca/{query};kw"
DCZ_PACKAGE_URL = "https://data.gov.ua/api/3/action/package_show"
DCZ_DATASET_ID = "a95174b2-ff4b-43f8-bee2-a89d3a258215"
DOU_SURVEY_URL = "https://raw.githubusercontent.com/devua/csv/master/salaries/{name}"
DOU_SURVEY_INDEX = "https://api.github.com/repos/devua/csv/contents/salaries"
NBU_RATE_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"


class MarketProviderError(RuntimeError):
    """A provider could not return enough real salary observations."""


@dataclass
class SalarySample:
    """Monthly gross (or contract) salary observations in the snapshot currency."""
    monthly: list[Decimal]
    sources: list[dict]
    vacancy_count: int | None = None
    notes: list[str] = field(default_factory=list)


def _number(text: str) -> Decimal:
    return Decimal(re.sub(r"[^\d.,]", "", text).replace(",", "."))


def _clean(text: str) -> str:
    return (text.replace("&#8239;", "").replace("&thinsp;", "").replace("&nbsp;", " ")
            .replace(" ", "").replace(" ", "").replace("\xa0", " "))


def parse_salary_range(text: str) -> Decimal | None:
    """Midpoint of '9 000–11 985 zł' / '20 000 грн'; None for hourly or unparseable values."""
    cleaned = _clean(text).lower()
    if any(marker in cleaned for marker in ("godz", "/ h", "год.", "/hour")):
        return None
    numbers = [value for value in (_number(match) for match in re.findall(r"\d[\d ]*\d|\d", cleaned)) if value >= 500]
    if not numbers:
        return None
    return (numbers[0] + numbers[1]) / 2 if len(numbers) >= 2 else numbers[0]


class MarketIngestionService:
    def __init__(self, db_session: Session, client: httpx.Client | None = None):
        self.snapshots = MarketSnapshotService(db_session)
        self.client = client

    # ── HTTP ─────────────────────────────────────────────────────────
    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers = {"User-Agent": USER_AGENT, **kwargs.pop("headers", {})}
        if self.client is not None:
            response = self.client.request(method, url, headers=headers, **kwargs)
        else:
            with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
                response = client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    # ── Providers ────────────────────────────────────────────────────
    def _nofluffjobs(self, requirement: str) -> SalarySample:
        seen: dict[tuple, Decimal] = {}
        contract_types: set[str] = set()
        page, pages = 1, 1
        while page <= min(pages, 5):
            response = self._request(
                "POST", NOFLUFF_SEARCH_URL,
                params={"salaryCurrency": "PLN", "salaryPeriod": "month", "region": "pl"},
                json={"criteriaSearch": {"requirement": [requirement], "seniority": ["junior"]}, "page": page},
            )
            data = response.json()
            pages = int(data.get("totalPages") or 1)
            for posting in data.get("postings", []):
                salary = posting.get("salary") or {}
                if salary.get("currency") != "PLN" or str(salary.get("period", "")).lower() != "month":
                    continue
                low, high = salary.get("from"), salary.get("to")
                if not low:
                    continue
                key = (posting.get("title"), posting.get("name"), low, high)
                seen[key] = (Decimal(str(low)) + Decimal(str(high or low))) / 2
                contract_types.add(str(salary.get("type")))
            page += 1
        return SalarySample(
            monthly=list(seen.values()),
            vacancy_count=len(seen),
            sources=[{"name": "No Fluff Jobs, junior offers with disclosed salary", "reference": f"nofluffjobs:requirement={requirement};seniority=junior",
                      "url": f"https://nofluffjobs.com/pl/{requirement}?criteria=seniority%3Djunior"}],
            notes=[f"Contract types in sample: {', '.join(sorted(contract_types))}. B2B rates are invoice amounts before tax."],
        )

    def _pracuj(self, query: str) -> SalarySample:
        values: dict[tuple, Decimal] = {}
        for page in (1, 2, 3):
            response = self._request("GET", PRACUJ_URL.format(query=query), params={"et": "17", "pn": page})
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.S)
            if not match:
                break
            offers = list(_find_offers(json.loads(match.group(1))))
            if not offers:
                break
            for offer in offers:
                text = offer.get("salaryDisplayText") or ""
                if "mies" not in text:
                    continue
                value = parse_salary_range(text)
                if value is not None:
                    values[(offer.get("jobTitle"), offer.get("companyName"), text)] = value
        return SalarySample(
            monthly=list(values.values()), vacancy_count=len(values),
            sources=[{"name": "Pracuj.pl, junior offers with disclosed monthly salary", "reference": f"pracuj:{query};et=17",
                      "url": f"https://www.pracuj.pl/praca/{query};kw?et=17"}],
            notes=["Mix of employment contracts (umowa o pracę, zlecenie, B2B) as published by employers."],
        )

    def _state_employment_service(self, profession_pattern: str) -> SalarySample:
        """Official daily vacancy register of the State Employment Service (data.gov.ua), streamed."""
        package = self._request("GET", DCZ_PACKAGE_URL, params={"id": DCZ_DATASET_ID}).json()["result"]
        resources = [item for item in package["resources"] if str(item.get("format", "")).upper() == "XML"]
        latest = max(resources, key=lambda item: item.get("created") or "")
        matcher = re.compile(profession_pattern, re.I)
        values: dict[str, Decimal] = {}

        def text_of(job, tag: str) -> str:
            node = job.find(tag)
            return re.sub(r"^!\[CDATA\[|\]\]$", "", (node.text or "").strip()) if node is not None else ""

        parser = ElementTree.XMLPullParser(events=("end",))
        stream = self.client.stream("GET", latest["url"], headers={"User-Agent": USER_AGENT}) if self.client else httpx.stream(
            "GET", latest["url"], headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(120.0), follow_redirects=True)
        with stream as response:
            response.raise_for_status()
            for chunk in response.iter_bytes():
                parser.feed(chunk)
                for _, element in parser.read_events():
                    if element.tag != "job":
                        continue
                    salary = text_of(element, "salary")
                    if matcher.search(text_of(element, "name")) and "місяць" in salary:
                        value = parse_salary_range(salary)
                        if value is not None:
                            values[element.get("id") or text_of(element, "link")] = value
                    element.clear()
        return SalarySample(
            monthly=list(values.values()), vacancy_count=len(values),
            sources=[{"name": "State Employment Service of Ukraine, register of current vacancies", "reference": f"dcz:{latest.get('id')}",
                      "url": f"https://data.gov.ua/dataset/{DCZ_DATASET_ID}"}],
            notes=["Vacancies registered with employment centres; the register does not state required experience."],
        )

    def _dou_python_junior(self) -> SalarySample:
        files = self._request("GET", DOU_SURVEY_INDEX).json()
        latest = sorted(item["name"] for item in files if item["name"].endswith("_raw.csv"))[-1]
        text = self._request("GET", DOU_SURVEY_URL.format(name=latest)).content.decode("utf-8")
        reader = csv.reader(io.StringIO(text))
        header = next(reader)

        def column(prefix: str) -> int:
            return next(index for index, name in enumerate(header) if name.strip().startswith(prefix))

        salary_col, language_col, title_col = column("ЗАРПЛАТА"), column("Основна мова"), column("Title_clean")
        employment_col, residence_col = column("Ваша основна зайнятість"), column("Де ви зараз живете")
        usd = [
            Decimal(row[salary_col]) for row in reader
            if len(row) > residence_col and row[language_col] == "Python" and row[title_col] == "Junior"
            and row[employment_col].startswith("Працюю в ІТ") and row[residence_col] == "В Україні"
            and row[salary_col].strip().isdigit()
        ]
        rate_data = self._request("GET", NBU_RATE_URL, params={"valcode": "USD", "json": ""}).json()
        rate = Decimal(str(rate_data[0]["rate"]))
        survey = latest.removesuffix("_raw.csv")
        return SalarySample(
            monthly=[value * rate for value in usd],
            vacancy_count=None,
            sources=[
                {"name": f"DOU salary survey {survey}, Python juniors living in Ukraine", "reference": f"dou:{latest}",
                 "url": f"https://github.com/devua/csv/blob/master/salaries/{latest}"},
                {"name": f"NBU official USD rate {rate_data[0].get('exchangedate')}", "reference": f"nbu:USD:{rate}",
                 "url": "https://bank.gov.ua/en/markets/exchangerates"},
            ],
            notes=["Survey answers are monthly income in USD converted at the NBU rate."],
        )

    def providers(self) -> dict[tuple[str, str], tuple[str, Callable[[], SalarySample]]]:
        """(role, country) → (currency, provider); seniority per provider lives in PROVIDER_SENIORITY."""
        return {
            ("python backend developer", "poland"): ("PLN", lambda: self._nofluffjobs("python")),
            ("lawyer", "poland"): ("PLN", lambda: self._pracuj("prawnik")),
            ("python backend developer", "ukraine"): ("UAH", self._dou_python_junior),
            ("lawyer", "ukraine"): ("UAH", lambda: self._state_employment_service(r"^(юрист|юрисконсульт)")),
        }

    # ── Snapshot ─────────────────────────────────────────────────────
    @staticmethod
    def build_payload(role: str, country: str, currency: str, sample: SalarySample, today: date | None = None, seniority: str = SENIORITY) -> MarketSnapshotCreateRequest:
        if len(sample.monthly) < MIN_SAMPLE:
            raise MarketProviderError(f"Only {len(sample.monthly)} salary observations for {role} in {country}; need {MIN_SAMPLE}")
        values = sorted(float(value) for value in sample.monthly)
        q1, _, q3 = quantiles(values, n=4, method="inclusive")

        def annual(monthly: float) -> Decimal:
            return (Decimal(str(monthly)) * 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        size = len(values)
        now = datetime.now(UTC)
        sources = [{**source, "acquired_at": now.isoformat()} for source in sample.sources]
        return MarketSnapshotCreateRequest(
            role=role, country=country, seniority=seniority, snapshot_date=today or now.date(), currency=currency,
            salary_min=annual(q1), median_salary=annual(median(values)), salary_max=annual(q3),
            vacancy_count=sample.vacancy_count, sources=sources, acquired_at=now, sample_size=size,
            confidence="low" if size < 10 else "medium" if size < 30 else "high",
            methodology_version=METHODOLOGY_VERSION,
        )

    def fetch_live(self, role: str, country: str, currency: str | None = None) -> tuple[MarketSnapshot, bool] | None:
        entry = self.providers().get((role.strip().casefold(), country.strip().casefold()))
        if entry is None:
            logger.info("No live salary provider for %s in %s", role, country)
            return None
        provider_currency, provider = entry
        if currency and currency.upper() != provider_currency:
            logger.info("Provider for %s in %s reports %s, scenario uses %s", role, country, provider_currency, currency)
            return None
        sample = provider()
        canonical_role = next(name for name in SUPPORTED_ROLES if name.casefold() == role.strip().casefold())
        canonical_country = country.strip().title()
        seniority = PROVIDER_SENIORITY.get((role.strip().casefold(), country.strip().casefold()), SENIORITY)
        payload = self.build_payload(canonical_role, canonical_country, provider_currency, sample, seniority=seniority)
        return self.snapshots.create(payload)


SUPPORTED_ROLES = ("Python Backend Developer", "Lawyer")
PROVIDER_SENIORITY = {("lawyer", "ukraine"): ALL_LEVELS}


def _find_offers(node):
    if isinstance(node, dict):
        if "jobTitle" in node and "salaryDisplayText" in node:
            yield node
        for value in node.values():
            yield from _find_offers(value)
    elif isinstance(node, list):
        for value in node:
            yield from _find_offers(value)
