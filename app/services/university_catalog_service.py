"""University directory: names, countries and official domains from the open
university-domains-list dataset (the data behind universities.hipolabs.com), stored locally
so the live search answers from Postgres instead of a slow remote API."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import University

logger = logging.getLogger(__name__)

DIRECTORY_URL = "https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json"
DIRECTORY_SOURCE = "university-domains-list"
IMPORTED_COUNTRIES = ("Poland", "Ukraine")
TIMEOUT = httpx.Timeout(30.0)


class UniversityCatalogService:
    def __init__(self, db_session: Session, client: httpx.Client | None = None) -> None:
        self.db = db_session
        self.client = client

    def _download(self) -> list[dict[str, Any]]:
        if self.client is not None:
            response = self.client.get(DIRECTORY_URL)
        else:
            with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
                response = client.get(DIRECTORY_URL)
        response.raise_for_status()
        return response.json()

    def has_directory(self, country: str) -> bool:
        return bool(self.db.scalar(
            select(func.count()).select_from(University)
            .where(func.lower(University.country) == country.casefold(), University.source == DIRECTORY_SOURCE)
        ))

    def import_countries(self, countries: tuple[str, ...] = IMPORTED_COUNTRIES, rows: list[dict[str, Any]] | None = None) -> int:
        """Insert missing universities; existing rows (matched by country + name) only gain domains."""
        wanted = {country.casefold(): country for country in countries}
        rows = rows if rows is not None else self._download()
        existing = {
            (university.country.casefold(), university.name.casefold()): university
            for university in self.db.execute(
                select(University).where(func.lower(University.country).in_(list(wanted)))
            ).scalars()
        }
        added = 0
        for row in rows:
            country = wanted.get(str(row.get("country", "")).casefold())
            name = " ".join(str(row.get("name", "")).split())
            if not country or not name:
                continue
            domains = [domain for domain in row.get("domains") or [] if domain]
            website = (row.get("web_pages") or [None])[0]
            current = existing.get((country.casefold(), name.casefold()))
            if current is not None:
                current.domains = current.domains or domains
                current.website = current.website or website
                continue
            university = University(name=name[:255], country=country, website=website, domains=domains,
                                    state_province=row.get("state-province"), source=DIRECTORY_SOURCE)
            self.db.add(university)
            existing[(country.casefold(), name.casefold())] = university
            added += 1
        self.db.commit()
        return added

    def ensure_country(self, country: str) -> None:
        supported = next((name for name in IMPORTED_COUNTRIES if name.casefold() == country.casefold()), None)
        if supported and not self.has_directory(supported):
            try:
                self.import_countries((supported,))
            except httpx.HTTPError as error:
                logger.warning("University directory import failed for %s: %s", supported, error)
