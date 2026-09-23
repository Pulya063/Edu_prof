"""
external_api.py — інтеграція з зовнішніми API для університетів та вартості навчання.

Джерела:
  1. College Scorecard (api.data.gov) — університети США, вартість навчання по роках (2015–2023)
  2. Hipolabs Universities API — пошук університетів по всьому світу (назва, країна, сайт)
  3. TuitionPrice table — normalized yearly tuition data for non-US countries.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.core.logging_config import log_call

load_dotenv()
logger = logging.getLogger(__name__)

# ── Налаштування ─────────────────────────────────────────────────────────────

SCORECARD_KEY  = os.getenv("COLLEGE_SCORECARD_API_KEY", "DEMO_KEY")
SCORECARD_BASE = "https://api.data.gov/ed/collegescorecard/v1/schools"
HIPOLABS_BASE  = "http://universities.hipolabs.com/search"

# Роки для яких запитуємо дані з College Scorecard
SCORECARD_YEARS = [2018, 2019, 2020, 2021, 2022, 2023]

# Поля вартості на рік
def _year_fields(years: list[int]) -> str:
    fields = ["id", "school.name", "school.city", "school.state", "school.country"]
    for y in years:
        fields += [
            f"{y}.cost.tuition.in_state",
            f"{y}.cost.tuition.out_of_state",
            f"{y}.cost.avg_net_price.public",
            f"{y}.cost.avg_net_price.private",
        ]
    return ",".join(fields)


TIMEOUT = httpx.Timeout(8.0)


# ── Hipolabs: пошук університетів по всьому світу ───────────────────────────

@log_call
def search_universities_world(name: str, limit: int = 8) -> list[dict[str, Any]]:
    """
    Шукає університети за назвою через Hipolabs API.
    Повертає список {name, country, web_pages, source}.
    """
    logger.info("Calling Hipolabs university search")
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(HIPOLABS_BASE, params={"name": name, "limit": limit})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("Hipolabs university search failed")
        return []

    results = []
    for item in data[:limit]:
        results.append({
            "name":      item.get("name", ""),
            "country":   item.get("country", ""),
            "web_pages": item.get("web_pages", []),
            "source":    "hipolabs",
            "scorecard_id": None,
        })
    return results


# ── College Scorecard: пошук + вартість по роках (лише США) ─────────────────

@log_call
def search_universities_usa(name: str, limit: int = 8) -> list[dict[str, Any]]:
    """
    Шукає університети США через College Scorecard API.
    Повертає {name, city, state, scorecard_id, source}.
    """
    logger.info("Calling College Scorecard university search")
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                SCORECARD_BASE,
                params={
                    "api_key":     SCORECARD_KEY,
                    "school.name": name,
                    "fields":      "id,school.name,school.city,school.state",
                    "per_page":    limit,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("College Scorecard university search failed")
        return []

    results = []
    for item in data.get("results", []):
        results.append({
            "name":         item.get("school.name", ""),
            "country":      "United States",
            "city":         item.get("school.city", ""),
            "state":        item.get("school.state", ""),
            "scorecard_id": item.get("id"),
            "source":       "scorecard",
        })
    return results


@log_call
def get_tuition_history_usa(scorecard_id: int) -> list[dict[str, Any]]:
    """
    Повертає вартість навчання по роках (2018–2023) для конкретного
    американського університету через College Scorecard.
    """
    logger.info("Calling College Scorecard tuition history")
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                SCORECARD_BASE,
                params={
                    "api_key": SCORECARD_KEY,
                    "id":      scorecard_id,
                    "fields":  _year_fields(SCORECARD_YEARS),
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        logger.exception("College Scorecard tuition history failed")
        return []

    results_raw = data.get("results", [])
    if not results_raw:
        return []

    item = results_raw[0]
    history = []
    for year in SCORECARD_YEARS:
        in_state  = item.get(f"{year}.cost.tuition.in_state")
        out_state = item.get(f"{year}.cost.tuition.out_of_state")
        net_pub   = item.get(f"{year}.cost.avg_net_price.public")
        net_priv  = item.get(f"{year}.cost.avg_net_price.private")
        history.append({
            "year":             year,
            "tuition_in_state":      in_state,
            "tuition_out_of_state":  out_state,
            "avg_net_price":         net_pub or net_priv,
        })
    return history


@log_call
def get_tuition_history_non_us(country: str, db_session: Session) -> list[dict[str, Any]]:
    """
    Повертає середню вартість навчання по роках (2018–2023)
    для не-американських університетів з таблиці TuitionPrice.
    """
    from app.services.tuition_service import get_tuition_history

    return get_tuition_history(db_session, country)


# ── Єдиний публічний інтерфейс ───────────────────────────────────────────────

@log_call
def search_universities(name: str) -> list[dict[str, Any]]:
    """
    Шукає університети по всьому світу + США.
    USA-результати йдуть першими (мають дані по роках).
    """
    usa     = search_universities_usa(name, limit=5)
    world   = search_universities_world(name, limit=5)
    seen    = {u["name"].lower() for u in usa}
    world   = [u for u in world if u["name"].lower() not in seen]
    return usa + world


@log_call
def get_tuition_history(scorecard_id: int | None, country: str, db_session: Session) -> list[dict[str, Any]]:
    """
    Повертає вартість навчання по роках.
    Якщо є scorecard_id → College Scorecard (США).
    Інакше → таблиця TuitionPrice по країні.
    """
    if scorecard_id is not None:
        return get_tuition_history_usa(scorecard_id)
    return get_tuition_history_non_us(country, db_session)
