"""Verified facts for the top universities, read from app/data/university_facts.json.

Built by app.scripts.build_university_facts and reviewed before it is committed. Nothing here is
fetched at request time and nothing is estimated: a university not in the file simply has no facts.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StudyProgramme, University

FACTS_FILE = Path(__file__).resolve().parents[1] / "data" / "university_facts.json"
FACTS_SOURCE = "university-facts"


@lru_cache(maxsize=1)
def load_facts() -> list[dict[str, Any]]:
    if not FACTS_FILE.exists():
        return []
    return json.loads(FACTS_FILE.read_text(encoding="utf-8"))["universities"]


def _entry_domains(entry: dict[str, Any]) -> set[str]:
    return {entry["domain"], *entry.get("directory_domains", [])}


def _matches(domain: str, wanted: set[str]) -> bool:
    domain = domain.lower().removeprefix("www.")
    return any(domain == item or domain.endswith(f".{item}") for item in wanted)


def facts_for(university: University) -> dict[str, Any] | None:
    domains = list(university.domains or [])
    if university.website:
        domains.append(university.website.split("//")[-1].split("/")[0])
    return next((entry for entry in load_facts() if entry["country"] == university.country and any(_matches(item, _entry_domains(entry)) for item in domains)), None)


def ensure_catalogue_rows(db_session: Session) -> int:
    """The open directory misses some top universities; add those so their pages exist."""
    rows = list(db_session.execute(select(University)).scalars())
    added = 0
    for entry in load_facts():
        if any(university.country == entry["country"] and facts_for(university) is entry for university in rows):
            continue
        db_session.add(University(
            name=entry.get("registry_name_en") or entry["registry_name"], country=entry["country"], website=f"https://{entry['domain']}",
            source=FACTS_SOURCE, domains=[entry["domain"]],
        ))
        added += 1
    if added:
        db_session.commit()
    return added


def sync_programmes(db_session: Session) -> int:
    """Copy the reviewed programmes into the database. Safe to repeat: rows are replaced per university."""
    ensure_catalogue_rows(db_session)
    universities = list(db_session.execute(select(University)).scalars())
    stored = 0
    for entry in load_facts():
        row = next((item for item in universities if facts_for(item) is entry), None)
        if row is None:
            continue
        db_session.query(StudyProgramme).filter(StudyProgramme.university_id == row.id).delete()
        fees = entry.get("fees") or {}
        seen: dict[tuple, StudyProgramme] = {}
        def add(name: str, level: str | None, mode: str | None, fee: Any) -> None:
            key = (name[:500].casefold(), level, mode)
            if key not in seen:
                seen[key] = StudyProgramme(university_id=row.id, country=entry["country"], name=name[:500], level=level, study_mode=mode, annual_fee=fee, currency=fees.get("currency") if fee else None)
        for item in fees.get("programmes", []):
            add(item["programme"], item.get("level"), item.get("study_mode"), item["amount_per_year"])
        priced = {key[0] for key in seen}
        for item in entry.get("study_programmes", []):
            if item["name"].casefold() not in priced:
                add(item["name"], item.get("level"), None, None)
        db_session.add_all(seen.values())
        stored += len(seen)
    db_session.commit()
    return stored


def specializations(db_session: Session, country: str, university: str, query: str) -> dict[str, Any]:
    if db_session.query(StudyProgramme.id).first() is None:
        sync_programmes(db_session)
    row = None
    if university:
        row = db_session.execute(select(University).where(University.name == university, University.country == country)).scalars().first()
    statement = select(StudyProgramme)
    statement = statement.where(StudyProgramme.university_id == row.id) if row else statement.where(StudyProgramme.country == country)
    if query:
        statement = statement.where(StudyProgramme.name.ilike(f"%{query}%"))
    rows = db_session.execute(statement.order_by(StudyProgramme.name).limit(400)).scalars().all()
    if row:
        items = [{"name": item.name, "level": item.level, "annual_fee": item.annual_fee, "study_mode": item.study_mode} for item in rows]
    else:
        names = {item.name.casefold(): item.name for item in rows}
        items = [{"name": name} for name in names.values()]
    result: dict[str, Any] = {"items": items[:60], "fee_range": None, "address": None}
    facts = facts_for(row) if row else None
    if facts:
        address = facts["address"]
        result["address"] = ", ".join(part for part in (address.get("street"), " ".join(filter(None, (address.get("postal_code"), address.get("city"))))) if part)
        if facts.get("fees"):
            fees = facts["fees"]
            result["fee_range"] = {key: fees[key] for key in ("min_per_year", "max_per_year", "currency", "academic_year", "source_title", "source_url")}
    return result
