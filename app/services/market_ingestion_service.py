"""Live salary collection for the roles Fence supports, turned into validated market snapshots.

Every number comes from a public listing or survey and is reduced with plain statistics
(quartiles of monthly midpoints × 12). No source is invented or estimated by a model.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING
from urllib.parse import quote
from xml.etree import ElementTree

import httpx
from sqlalchemy.orm import Session

from app.models import MarketSnapshot
from app.schemas import MarketSnapshotCreateRequest
from app.services.market_snapshot_service import ALL_LEVELS, MarketSnapshotService

# numpy and pandas load only when a snapshot is actually built, so they stay out of the API process.
if TYPE_CHECKING:
    import numpy as np

# Only sorting and percentiles are used here; OpenBLAS otherwise reserves ~230 MB of per-thread buffers.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

logger = logging.getLogger(__name__)

METHODOLOGY_VERSION = "listing-quartiles-v2"
SENIORITY = "junior"
MIN_SAMPLE = 5
MEDIUM_SAMPLE = 10  # build_payload marks fewer observations as low confidence
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
        self._register_cache: tuple[list[tuple[str, Decimal]], dict] | None = None
        self._dou_cache: tuple[str, list[str], list[list[str]], dict] | None = None

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

    def _pracuj(self, query: str, junior: bool = True) -> SalarySample:
        """Pracuj.pl listings; junior=True keeps only the 'junior / assistant' level (et=17)."""
        values: dict[tuple, Decimal] = {}
        slug = quote(query)
        for page in (1, 2, 3):
            params = {"et": "17", "pn": page} if junior else {"pn": page}
            response = self._request("GET", PRACUJ_URL.format(query=slug), params=params)
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
            sources=[{"name": f"Pracuj.pl, {'junior' if junior else 'all-level'} offers for '{query}' with disclosed monthly salary",
                      "reference": f"pracuj:{query};{'et=17' if junior else 'all'}",
                      "url": f"https://www.pracuj.pl/praca/{slug};kw" + ("?et=17" if junior else "")}],
            notes=["Mix of employment contracts (umowa o pracę, zlecenie, B2B) as published by employers."],
        )

    def _register_rows(self) -> tuple[list[tuple[str, Decimal]], dict]:
        """All monthly-salary vacancies of the latest State Employment Service register (data.gov.ua).

        The XML is large, so it is streamed once per service instance and reused for every profession.
        """
        if self._register_cache is not None:
            return self._register_cache
        package = self._request("GET", DCZ_PACKAGE_URL, params={"id": DCZ_DATASET_ID}).json()["result"]
        resources = [item for item in package["resources"] if str(item.get("format", "")).upper() == "XML"]
        latest = max(resources, key=lambda item: item.get("created") or "")
        rows: dict[str, tuple[str, Decimal]] = {}

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
                    if "місяць" in salary:
                        value = parse_salary_range(salary)
                        if value is not None:
                            rows[element.get("id") or text_of(element, "link")] = (text_of(element, "name"), value)
                    element.clear()
        self._register_cache = (list(rows.values()), latest)
        return self._register_cache

    def _state_employment_service(self, profession_pattern: str) -> SalarySample:
        """Official daily vacancy register of the State Employment Service, filtered by job title."""
        rows, latest = self._register_rows()
        matcher = re.compile(profession_pattern, re.I)
        values = [value for name, value in rows if matcher.search(name)]
        return SalarySample(
            monthly=values, vacancy_count=len(values),
            sources=[{"name": "State Employment Service of Ukraine, register of current vacancies", "reference": f"dcz:{latest.get('id')}",
                      "url": f"https://data.gov.ua/dataset/{DCZ_DATASET_ID}"}],
            notes=["Vacancies registered with employment centres; the register does not state required experience."],
        )

    def _dou_survey(self) -> tuple[str, list[str], list[list[str]], dict]:
        if self._dou_cache is None:
            files = self._request("GET", DOU_SURVEY_INDEX).json()
            latest = sorted(item["name"] for item in files if item["name"].endswith("_raw.csv"))[-1]
            text = self._request("GET", DOU_SURVEY_URL.format(name=latest)).content.decode("utf-8")
            reader = csv.reader(io.StringIO(text))
            header = next(reader)
            rate = self._request("GET", NBU_RATE_URL, params={"valcode": "USD", "json": ""}).json()[0]
            self._dou_cache = (latest, header, list(reader), rate)
        return self._dou_cache

    def _dou_junior(self, label: str, column_prefix: str, accepted: tuple[str, ...]) -> SalarySample:
        """DOU salary survey: juniors living and working in IT in Ukraine whose answer in one column matches."""
        latest, header, rows, rate_data = self._dou_survey()

        def column(prefix: str) -> int:
            return next(index for index, name in enumerate(header) if name.strip().startswith(prefix))

        salary_col, title_col, filter_col = column("ЗАРПЛАТА"), column("Title_clean"), column(column_prefix)
        employment_col, residence_col = column("Ваша основна зайнятість"), column("Де ви зараз живете")
        usd = [
            Decimal(row[salary_col]) for row in rows
            if len(row) > max(residence_col, filter_col) and row[filter_col] in accepted and row[title_col] == "Junior"
            and row[employment_col].startswith("Працюю в ІТ") and row[residence_col] == "В Україні"
            and row[salary_col].strip().isdigit()
        ]
        rate = Decimal(str(rate_data["rate"]))
        survey = latest.removesuffix("_raw.csv")
        return SalarySample(
            monthly=[value * rate for value in usd],
            vacancy_count=None,
            sources=[
                {"name": f"DOU salary survey {survey}, {label} juniors living in Ukraine", "reference": f"dou:{latest}:{'|'.join(accepted)}",
                 "url": f"https://github.com/devua/csv/blob/master/salaries/{latest}"},
                {"name": f"NBU official USD rate {rate_data.get('exchangedate')}", "reference": f"nbu:USD:{rate}",
                 "url": "https://bank.gov.ua/en/markets/exchangerates"},
            ],
            notes=["Survey answers are monthly income in USD converted at the NBU rate."],
        )

    def _dou_python_junior(self) -> SalarySample:
        return self._dou_junior("Python", "Основна мова", ("Python",))

    @staticmethod
    def _combine(*samples: SalarySample) -> SalarySample:
        """Pool observations from several listings of the same level; each source stays cited."""
        return SalarySample(
            monthly=[value for sample in samples for value in sample.monthly],
            sources=[source for sample in samples if sample.monthly for source in sample.sources],
            vacancy_count=sum(sample.vacancy_count or 0 for sample in samples) or None,
            notes=[note for sample in samples if sample.monthly for note in sample.notes],
        )

    def _source(self, source: tuple) -> SalarySample:
        kind, *args = source
        if kind == "nofluff":
            return self._nofluffjobs(*args)
        if kind == "pracuj":
            return self._pracuj(args[0], junior=True)
        if kind == "pracuj_all":
            return self._pracuj(args[0], junior=False)
        if kind == "register":
            return self._state_employment_service(*args)
        if kind == "dou":
            return self._dou_junior(*args)
        raise ValueError(f"Unknown salary source {kind}")

    def providers(self) -> dict[tuple[str, str], tuple[str, list[tuple[str, list[tuple]]]]]:
        """(role, country) -> (currency, tiers). A tier is (seniority, sources pooled together)."""
        table: dict[tuple[str, str], tuple[str, list[tuple[str, list[tuple]]]]] = {}
        for role, spec in ROLE_CATALOG.items():
            for country, currency in (("poland", "PLN"), ("ukraine", "UAH")):
                if spec.get(country):
                    table[(role.casefold(), country)] = (currency, spec[country])
        return table

    def collect(self, role: str, country: str) -> tuple[str, str, SalarySample]:
        """(currency, seniority, sample): the first tier with MEDIUM_SAMPLE clean observations, otherwise
        the first with MIN_SAMPLE. A broader level with a solid sample beats a thin junior one."""
        entry = self.providers().get((role.strip().casefold(), country.strip().casefold()))
        if entry is None:
            raise MarketProviderError(f"No live salary provider for {role} in {country}")
        currency, tiers = entry
        reasons: list[str] = []
        fallback: tuple[str, str, SalarySample] | None = None
        for seniority, sources in tiers:
            samples: list[SalarySample] = []
            for source in sources:
                try:
                    samples.append(self._source(source))
                except (httpx.HTTPError, ValueError, KeyError, IndexError, StopIteration) as error:
                    reasons.append(f"{source[0]} failed: {type(error).__name__}")
            pooled = self._combine(*samples) if samples else SalarySample(monthly=[], sources=[])
            usable = len(self.clean_observations(pooled.monthly))
            if usable >= MEDIUM_SAMPLE:
                return currency, seniority, pooled
            if usable >= MIN_SAMPLE and fallback is None:
                fallback = (currency, seniority, pooled)
            reasons.append(f"{seniority}: {usable} observations")
        if fallback is not None:
            return fallback
        raise MarketProviderError(f"Not enough salary observations for {role} in {country} ({'; '.join(reasons)})")

    # ── Snapshot ─────────────────────────────────────────────────────
    @staticmethod
    def clean_observations(monthly: list[Decimal]) -> np.ndarray:
        """Positive monthly values with typo-sized outliers removed.

        Tukey's far-out fences (Q1 - 3·IQR, Q3 + 3·IQR) drop entries such as an annual figure typed into a
        monthly field, while every plausible salary stays. Needs 8+ values to estimate the fences.
        """
        import numpy as np
        import pandas as pd

        series = pd.to_numeric(pd.Series([float(value) for value in monthly], dtype="float64"), errors="coerce").dropna()
        series = series[series > 0]
        if len(series) >= 8:
            q1, q3 = np.percentile(series.to_numpy(), [25, 75], method="linear")
            spread = q3 - q1
            series = series[(series >= q1 - 3 * spread) & (series <= q3 + 3 * spread)]
        return np.sort(series.to_numpy())

    @staticmethod
    def build_payload(role: str, country: str, currency: str, sample: SalarySample, today: date | None = None, seniority: str = SENIORITY) -> MarketSnapshotCreateRequest:
        import numpy as np

        values = MarketIngestionService.clean_observations(sample.monthly)
        if len(values) < MIN_SAMPLE:
            raise MarketProviderError(f"Only {len(values)} salary observations for {role} in {country}; need {MIN_SAMPLE}")
        # Linear interpolation equals statistics.quantiles(method="inclusive").
        q1, mid, q3 = np.percentile(values, [25, 50, 75], method="linear")

        def annual(monthly: float) -> Decimal:
            return (Decimal(str(round(float(monthly), 6))) * 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        size = int(len(values))
        now = datetime.now(UTC)
        sources = [{**source, "acquired_at": now.isoformat()} for source in sample.sources]
        return MarketSnapshotCreateRequest(
            role=role, country=country, seniority=seniority, snapshot_date=today or now.date(), currency=currency,
            salary_min=annual(q1), median_salary=annual(mid), salary_max=annual(q3),
            vacancy_count=sample.vacancy_count, sources=sources, acquired_at=now, sample_size=size,
            confidence="low" if size < MEDIUM_SAMPLE else "medium" if size < 30 else "high",
            methodology_version=METHODOLOGY_VERSION,
        )

    def fetch_live(self, role: str, country: str, currency: str | None = None) -> tuple[MarketSnapshot, bool] | None:
        entry = self.providers().get((role.strip().casefold(), country.strip().casefold()))
        if entry is None:
            logger.info("No live salary provider for %s in %s", role, country)
            return None
        if currency and currency.upper() != entry[0]:
            logger.info("Provider for %s in %s reports %s, scenario uses %s", role, country, entry[0], currency)
            return None
        provider_currency, seniority, sample = self.collect(role, country)
        canonical_role = next(name for name in SUPPORTED_ROLES if name.casefold() == role.strip().casefold())
        payload = self.build_payload(canonical_role, country.strip().title(), provider_currency, sample, seniority=seniority)
        return self.snapshots.create(payload)


def _it_role(nofluff: str | None, pracuj: str, dou: tuple) -> dict:
    junior_pl = ([("nofluff", nofluff)] if nofluff else []) + [("pracuj", pracuj)]
    return {
        "poland": [(SENIORITY, junior_pl), (ALL_LEVELS, [("pracuj_all", pracuj)])],
        "ukraine": [(SENIORITY, [("dou", *dou)]), (ALL_LEVELS, [("register", r"(програміст|розробник|аналітик|тестувальник)")])],
        "ses": ("OC2", "J"),
    }


def _role(pracuj: str, register: str, ses: tuple[str, str]) -> dict:
    return {
        "poland": [(SENIORITY, [("pracuj", pracuj)]), (ALL_LEVELS, [("pracuj_all", pracuj)])],
        "ukraine": [(ALL_LEVELS, [("register", register)])],
        "ses": ses,
    }


# Role catalogue. Poland: junior listings first, then all levels. Ukraine: DOU survey juniors for IT
# roles, the official vacancy register (all levels) otherwise. "ses" is the Eurostat Structure of
# Earnings Survey cell (ISCO-08 major group, NACE section) that OfficialWageService uses when the
# listings for Poland do not have enough observations.
ROLE_CATALOG: dict[str, dict] = {
    "Python Backend Developer": _it_role("python", "python developer", ("Python", "Основна мова", ("Python",))),
    "Frontend Developer": _it_role("javascript", "frontend developer", ("Front-end", "Спеціалізації", ("Front-end розробка",))),
    "Java Developer": _it_role("java", "java developer", ("Java", "Основна мова", ("Java",))),
    "QA Engineer": _it_role("testing", "tester", ("QA", "Категорії", ("QA",))),
    "Data Analyst": _it_role(None, "analityk danych", ("Analytics", "Категорії", ("Analytics",))),
    "Lawyer": _role("prawnik", r"^(юрист|юрисконсульт)", ("OC2", "M")),
    "Accountant": _role("księgowy", r"^(бухгалтер|головний бухгалтер)", ("OC3", "M")),
    "Marketing Specialist": _role("marketing", r"(маркетолог|фахівець з маркетингу|менеджер з маркетингу)", ("OC2", "M")),
    "Civil Engineer": _role("inżynier budowy", r"(інженер.{0,30}будів|будівельн.{0,10}інженер|інженер-будівельник|виконроб)", ("OC2", "F")),
    "Teacher": _role("nauczyciel", r"^(вчитель|учитель)", ("OC2", "P")),
    "Nurse": _role("pielęgniarka", r"(сестра медична|медична сестра|медсестра)", ("OC2", "Q")),
    "Doctor": _role("lekarz", r"^лікар", ("OC2", "Q")),
    "Pharmacist": _role("farmaceuta", r"(фармацевт|провізор)", ("OC2", "G")),
    "Psychologist": _role("psycholog", r"^психолог", ("OC2", "Q")),
}
SUPPORTED_ROLES = tuple(ROLE_CATALOG)

def _find_offers(node):
    if isinstance(node, dict):
        if "jobTitle" in node and "salaryDisplayText" in node:
            yield node
        for value in node.values():
            yield from _find_offers(value)
    elif isinstance(node, list):
        for value in node:
            yield from _find_offers(value)
