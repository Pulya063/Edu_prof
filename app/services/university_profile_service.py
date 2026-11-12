"""Public university profile: Wikidata facts, Wikipedia summary, Commons gallery, news, YouTube
and pages of the official website.

Everything is copied or parsed deterministically from the cited source. The official site is
crawled politely: robots.txt is honoured, at most a handful of pages, honest user agent.
"""

from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any
from urllib.parse import quote, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlalchemy.orm import Session

from app.models import University, UniversityProfile
from app.services import news_feed_service

logger = logging.getLogger(__name__)

BASE_USER_AGENT = "FenceBot/1.0 (education ROI research; respects robots.txt)"


def user_agent() -> str:
    """Wikimedia's robot policy requires a contact in the user agent; it comes from CRAWLER_CONTACT."""
    contact = os.getenv("CRAWLER_CONTACT", "").strip()
    return f"FenceBot/1.0 (+{contact}; education ROI research; respects robots.txt)" if contact else BASE_USER_AGENT
TIMEOUT = httpx.Timeout(10.0)
PROFILE_TTL = timedelta(days=7)
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_FILE = "https://commons.wikimedia.org/wiki/Special:FilePath/{name}?width={width}"
# Wikidata items for the countries whose catalogues Fence imports.
COUNTRY_ITEMS = {"poland": "Q36", "ukraine": "Q212"}
LANGUAGES = {"poland": "pl", "ukraine": "uk"}

PAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "admissions": ("rekrutac", "admission", "apply", "kandyda", "вступ", "абітурієнт", "приймальн"),
    "scholarships": ("stypend", "scholarship", "стипенд"),
    "fees": ("opłat", "oplat", "czesne", "tuition", "fees", "вартість", "оплат", "платн"),
    "sport": ("sport", "azs", "спорт"),
    "faculties": ("wydzia", "faculty", "faculties", "факультет", "інститути"),
    "international": ("international", "foreign", "cudzoziem", "іноземн", "erasmus"),
    "news": ("aktualnosci", "aktualności", "news", "новини"),
}
DOCUMENT_KEYWORDS = ("świadectw", "swiadectw", "matur", "paszport", "passport", "certificate", "diploma", "dyplom",
                     "zdjęci", "photo", "transcript", "атестат", "паспорт", "сертифікат", "нмт", "зно", "диплом",
                     "фото", "ідентифікац", "довідк", "legaliz", "apostil", "апостил")
DOCUMENT_HINTS = ("dokument", "wymagan", "required", "документ", "перелік")
AMOUNT_PATTERN = re.compile(r"(\d{1,3}(?:[  .]\d{3})+|\d{3,6})(?:[.,]\d{2})?\s?(zł|pln|eur|€|грн|uah|usd|\$)", re.I)
CURRENCIES = {"zł": "PLN", "pln": "PLN", "eur": "EUR", "€": "EUR", "грн": "UAH", "uah": "UAH", "usd": "USD", "$": "USD"}


class _PageParser(HTMLParser):
    """Collects links and readable text blocks without any third-party parser."""

    BLOCKS = {"p", "li", "td", "h1", "h2", "h3", "h4", "dd", "dt"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.blocks: list[str] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._block: list[str] | None = None
        self._skip = 0
        self.final_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []
        elif tag in self.BLOCKS:
            self._block = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip = max(0, self._skip - 1)
        elif tag == "a" and self._href:
            self.links.append((self._href, " ".join("".join(self._link_text).split())))
            self._href = None
        elif tag in self.BLOCKS and self._block is not None:
            text = " ".join("".join(self._block).split())
            if text:
                self.blocks.append(text)
            self._block = None

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._href is not None:
            self._link_text.append(data)
        if self._block is not None:
            self._block.append(data)


def parse_page(html: str) -> _PageParser:
    parser = _PageParser()
    parser.feed(html)
    return parser


ARTICLE_SEGMENTS = ("aktualnosci/", "news/", "novyny/", "новини/", "wydarzenia/", "events/", "blog/")
EXCLUDED_FOR_ADMISSIONS = ("do-pracy", "praca", "career", "kariera", "job", "вакансі", "pracownic")


def classify_links(base_url: str, links: list[tuple[str, str]], per_kind: int = 2) -> list[dict[str, str]]:
    """Section pages by keyword; navigation pages (short paths) beat individual news articles."""
    host = urlparse(base_url).netloc.removeprefix("www.")
    candidates: dict[str, list[tuple[int, str, str]]] = {kind: [] for kind in PAGE_KEYWORDS}
    seen: set[str] = set()
    for href, text in links:
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = urljoin(base_url, href).split("#")[0]
        parsed = urlparse(url)
        if not parsed.netloc.removeprefix("www.").endswith(host) or url in seen:
            continue
        path = parsed.path.casefold()
        if not re.sub(r"^/?([a-z]{2}/?)?", "", path).strip("/") and parsed.netloc.removeprefix("www.") == host:
            continue  # the home page (or its language root) is not a section
        haystack = f"{url} {text}".casefold()
        is_article = any(segment in path for segment in ARTICLE_SEGMENTS)
        depth = len([part for part in path.split("/") if part]) + (0 if parsed.netloc.removeprefix("www.") == host else 1)
        for kind, keywords in PAGE_KEYWORDS.items():
            if not any(keyword in haystack for keyword in keywords):
                continue
            if kind != "news" and is_article:
                continue
            if kind == "admissions" and any(word in haystack for word in EXCLUDED_FOR_ADMISSIONS):
                continue
            candidates[kind].append((depth, text[:120] or url, url))
            seen.add(url)
            break
    found = []
    for kind, items in candidates.items():
        for _, title, url in sorted(items, key=lambda item: (item[0], len(item[1])))[:per_kind]:
            found.append({"kind": kind, "title": title, "url": url})
    return found


def tuition_mentions(blocks: list[str], source_url: str, limit: int = 8) -> list[dict[str, Any]]:
    mentions = []
    for block in blocks:
        for match in AMOUNT_PATTERN.finditer(block):
            raw = re.sub(r"[  .]", "", match.group(1))
            try:
                amount = Decimal(raw)
            except InvalidOperation:
                continue
            if amount < 100:
                continue
            context = block[max(0, match.start() - 90): match.end() + 60].casefold()
            period = ("year" if re.search(r"\brok|year|annual|рік|річн", context)
                      else "semester" if re.search(r"semest|семестр", context)
                      else "month" if re.search(r"miesi|month|місяц", context) else "unknown")
            mentions.append({"text": block[:240], "source_url": source_url, "amount": amount,
                             "currency": CURRENCIES[match.group(2).casefold()], "period": period})
            if len(mentions) >= limit:
                return mentions
    return mentions


def keyword_blocks(blocks: list[str], keywords: tuple[str, ...], source_url: str, limit: int, min_hits: int = 1) -> list[dict[str, str]]:
    result, seen = [], set()
    for block in blocks:
        lowered = block.casefold()
        hits = sum(keyword in lowered for keyword in keywords)
        if 20 <= len(block) <= 300 and hits >= min_hits and lowered not in seen:
            seen.add(lowered)
            result.append({"text": block, "source_url": source_url})
            if len(result) >= limit:
                break
    return result


class UniversityProfileService:
    def __init__(self, db_session: Session, client: httpx.Client | None = None) -> None:
        self.db = db_session
        self.client = client
        self._robots: dict[str, RobotFileParser | None] = {}

    # ── HTTP ─────────────────────────────────────────────────────────
    def _get(self, url: str, params: dict[str, Any] | None = None) -> httpx.Response:
        headers = {"User-Agent": user_agent()}
        if self.client is not None:
            response = self.client.get(url, params=params, headers=headers)
        else:
            with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
                response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response

    def _allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            robots = RobotFileParser()
            try:
                robots.parse(self._get(f"{origin}/robots.txt").text.splitlines())
            except httpx.HTTPStatusError as error:
                # A missing robots.txt allows crawling; an auth/forbidden answer means stay out.
                robots = None if error.response.status_code in {401, 403} else RobotFileParser()
                if robots is not None:
                    robots.parse([])
            except httpx.HTTPError:
                robots = None
            self._robots[origin] = robots
        robots = self._robots[origin]
        return robots is not None and robots.can_fetch("FenceBot", url)

    # ── Wikidata / Wikipedia / Commons ───────────────────────────────
    def _wikidata(self, university: University) -> dict[str, Any] | None:
        country_item = COUNTRY_ITEMS.get(university.country.casefold())
        languages = ["en", LANGUAGES.get(university.country.casefold(), "en")]
        candidates: list[str] = []
        for language in dict.fromkeys(languages):
            data = self._get(WIKIDATA_API, {"action": "wbsearchentities", "search": university.name, "language": language,
                                            "type": "item", "limit": 5, "format": "json"}).json()
            candidates += [item["id"] for item in data.get("search", []) if item["id"] not in candidates]
        if not candidates:
            return None
        entities = self._get(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(candidates[:8]), "props": "claims|sitelinks|labels",
                                            "languages": "en|pl|uk", "format": "json"}).json().get("entities", {})
        domains = {domain.removeprefix("www.") for domain in (university.domains or [])}

        def claim_values(entity: dict, prop: str) -> list[Any]:
            return [claim["mainsnak"].get("datavalue", {}).get("value") for claim in entity.get("claims", {}).get(prop, [])
                    if claim["mainsnak"].get("datavalue")]

        def score(entity: dict) -> int:
            countries = {value.get("id") for value in claim_values(entity, "P17") if isinstance(value, dict)}
            websites = {urlparse(value).netloc.removeprefix("www.") for value in claim_values(entity, "P856") if isinstance(value, str)}
            return (2 if country_item in countries else 0) + (3 if domains & websites else 0)

        best = max((entities[qid] for qid in candidates[:8] if qid in entities), key=score, default=None)
        if best is None or score(best) == 0:
            return None
        return {"entity": best, "claims": claim_values}

    def _labels(self, ids: list[str]) -> dict[str, str]:
        if not ids:
            return {}
        data = self._get(WIKIDATA_API, {"action": "wbgetentities", "ids": "|".join(ids[:50]), "props": "labels",
                                        "languages": "en|pl|uk", "format": "json"}).json().get("entities", {})
        labels = {}
        for qid, entity in data.items():
            values = entity.get("labels", {})
            label = next((values[lang]["value"] for lang in ("en", "pl", "uk") if lang in values), None)
            if label:
                labels[qid] = label
        return labels

    def _wikipedia(self, sitelinks: dict[str, Any], country: str) -> dict[str, str] | None:
        for lang in ("en", LANGUAGES.get(country.casefold(), "en")):
            link = sitelinks.get(f"{lang}wiki")
            if not link:
                continue
            data = self._get(WIKIPEDIA_SUMMARY.format(lang=lang, title=quote(link["title"].replace(" ", "_")))).json()
            if data.get("extract"):
                return {"summary": data["extract"], "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")}
        return None

    def _gallery(self, category: str) -> list[dict[str, str]]:
        data = self._get(COMMONS_API, {"action": "query", "generator": "categorymembers", "gcmtitle": f"Category:{category}",
                                       "gcmtype": "file", "gcmlimit": 16, "prop": "imageinfo", "iiprop": "url",
                                       "iiurlwidth": 480, "format": "json"}).json()
        images = []
        for page in (data.get("query", {}).get("pages", {}) or {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            title = page.get("title", "")
            if not re.search(r"\.(jpe?g|png|webp)$", title, re.I) or not info.get("thumburl"):
                continue
            images.append({"title": re.sub(r"^File:|\.\w+$", "", title), "url": info["url"], "thumb_url": info["thumburl"],
                           "source_url": info.get("descriptionurl", "")})
            if len(images) >= 8:
                break
        return images

    def _collect_wikimedia(self, university: University, profile: dict[str, Any]) -> str | None:
        """Fills facts, faculties, summary and gallery; returns the YouTube channel id if Wikidata lists one."""
        match = self._wikidata(university)
        if match is None:
            profile["unavailable_sources"].append("Wikidata: no matching item")
            return None
        entity, claims = match["entity"], match["claims"]
        qid = entity["id"]
        profile["wikidata_url"] = f"https://www.wikidata.org/wiki/{qid}"
        profile["sources"].append({"title": "Wikidata", "url": profile["wikidata_url"]})

        facts = profile["facts"]
        inception = next((value.get("time") for value in claims(entity, "P571") if isinstance(value, dict)), None)
        facts["founded"] = inception[1:5].lstrip("0") if inception else None
        for prop, key in (("P2196", "students"), ("P1128", "staff")):
            amounts = [value for value in claims(entity, prop) if isinstance(value, dict) and value.get("amount")]
            if amounts:
                facts[key] = int(Decimal(amounts[-1]["amount"]))
        for prop, key in (("P154", "logo_url"), ("P18", "image_url")):
            name = next((value for value in claims(entity, prop) if isinstance(value, str)), None)
            if name:
                facts[key] = COMMONS_FILE.format(name=quote(name.replace(" ", "_")), width=640)
        if not university.website:
            profile["website"] = next((value for value in claims(entity, "P856") if isinstance(value, str)), None)

        place_ids = [value["id"] for value in claims(entity, "P131") if isinstance(value, dict)]
        part_ids = [value["id"] for prop in ("P355", "P527") for value in claims(entity, prop) if isinstance(value, dict)]
        labels = self._labels(place_ids[:1] + part_ids)
        facts["city"] = labels.get(place_ids[0]) if place_ids else None
        profile["faculties"] = [labels[qid] for qid in part_ids if qid in labels][:30]

        wiki = self._wikipedia(entity.get("sitelinks", {}), university.country)
        if wiki:
            profile["summary"], profile["summary_source_url"] = wiki["summary"], wiki["url"]
            profile["sources"].append({"title": "Wikipedia", "url": wiki["url"]})

        category = next((value for value in claims(entity, "P373") if isinstance(value, str)), None)
        if category:
            profile["gallery"] = self._gallery(category)
            if profile["gallery"]:
                profile["sources"].append({"title": "Wikimedia Commons", "url": f"https://commons.wikimedia.org/wiki/Category:{quote(category)}"})
        return next((value for value in claims(entity, "P2397") if isinstance(value, str)), None)

    # ── Official website ─────────────────────────────────────────────
    def _page(self, url: str) -> _PageParser | None:
        if not self._allowed(url):
            return None
        response = self._get(url)
        if "html" not in response.headers.get("content-type", "html"):
            return None
        page = parse_page(response.text)
        page.final_url = str(response.url)
        return page

    def _collect_site(self, website: str, profile: dict[str, Any]) -> None:
        home_url = website if website.startswith("http") else f"https://{website}"
        home = self._page(home_url)
        if home is None:
            profile["unavailable_sources"].append("Official website: blocked by robots.txt or not HTML")
            return
        home_url = home.final_url or home_url
        profile["sources"].append({"title": "Official website", "url": home_url})
        pages = classify_links(home_url, home.links)
        profile["official_pages"] = pages

        def first(kind: str) -> str | None:
            return next((page["url"] for page in pages if page["kind"] == kind), None)

        for kind in ("admissions", "fees", "scholarships", "sport", "faculties"):
            url = first(kind)
            if not url:
                continue
            try:
                page = self._page(url)
            except httpx.HTTPError as error:
                logger.info("University page %s unavailable: %s", url, error)
                continue
            if page is None:
                continue
            if kind == "admissions":
                # A general admissions page mentions documents in passing; ask for two document words there.
                profile["admission_documents"] = keyword_blocks(page.blocks, DOCUMENT_KEYWORDS, url, 10, min_hits=2)
                profile["tuition_mentions"] += tuition_mentions(page.blocks, url, 4)
                # One hop deeper (at most 4 pages): candidate portals keep document lists and fees on their own pages.
                hops = 0
                for href, text in page.links:
                    if hops >= 4:
                        break
                    target = urljoin(url, href)
                    haystack = f"{target} {text}".casefold()
                    wants_documents = not profile["admission_documents"] and any(word in haystack for word in DOCUMENT_HINTS)
                    wants_fees = not first("fees") and any(word in haystack for word in PAGE_KEYWORDS["fees"])
                    if not (wants_documents or wants_fees) or urlparse(target).netloc.removeprefix("www.").split(".")[-2:] != urlparse(url).netloc.removeprefix("www.").split(".")[-2:]:
                        continue
                    hops += 1
                    try:
                        deeper = self._page(target)
                    except httpx.HTTPError:
                        continue
                    if deeper is None:
                        continue
                    if wants_documents:
                        profile["admission_documents"] = keyword_blocks(deeper.blocks, DOCUMENT_KEYWORDS, target, 10)
                    if wants_fees:
                        profile["tuition_mentions"] += tuition_mentions(deeper.blocks, target)
                        pages.append({"kind": "fees", "title": text[:120] or target, "url": target})
                    if profile["admission_documents"] and first("fees"):
                        break
            elif kind == "fees":
                profile["tuition_mentions"] += tuition_mentions(page.blocks, url)
            elif kind == "scholarships":
                profile["scholarship_mentions"] = keyword_blocks(page.blocks, PAGE_KEYWORDS["scholarships"], url, 6)
            elif kind == "sport":
                profile["sport_mentions"] = keyword_blocks(page.blocks, PAGE_KEYWORDS["sport"], url, 6)
            elif kind == "faculties" and not profile["faculties"]:
                profile["faculties"] = list(dict.fromkeys(
                    text for _, text in page.links
                    if re.match(r"^(wydział|faculty|факультет|інститут)\s+\S", text, re.I)
                ))[:30]

    # ── Orchestration ────────────────────────────────────────────────
    def collect(self, university: University) -> dict[str, Any]:
        profile: dict[str, Any] = {
            "summary": None, "summary_source_url": None, "wikidata_url": None, "website": university.website,
            "facts": {"founded": None, "students": None, "staff": None, "city": None, "logo_url": None, "image_url": None},
            "faculties": [], "official_pages": [], "admission_documents": [], "scholarship_mentions": [],
            "tuition_mentions": [], "sport_mentions": [], "news": [], "videos": [], "gallery": [],
            "sources": [], "unavailable_sources": [],
        }

        def wikimedia() -> str | None:
            try:
                return self._collect_wikimedia(university, profile)
            except httpx.HTTPError as error:
                blocked = isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 403
                profile["unavailable_sources"].append(
                    "Wikimedia: not configured (set CRAWLER_CONTACT, required by the Wikimedia robot policy)"
                    if blocked and not os.getenv("CRAWLER_CONTACT") else f"Wikimedia: {type(error).__name__}"
                )
                return None

        def news() -> None:
            try:
                profile["news"] = news_feed_service.search_news(f'"{university.name}"', university.country, client=self.client)
                if profile["news"]:
                    profile["sources"].append({"title": "Google News", "url": news_feed_service.news_feed_url(f'"{university.name}"', university.country)})
            except Exception as error:
                profile["unavailable_sources"].append(f"News feed: {type(error).__name__}")

        with ThreadPoolExecutor(max_workers=2) as pool:
            channel_future = pool.submit(wikimedia)
            pool.submit(news).result()
            channel_id = channel_future.result()

        website = profile.get("website") or university.website
        if website:
            try:
                self._collect_site(website, profile)
            except httpx.HTTPError as error:
                profile["unavailable_sources"].append(f"Official website: {type(error).__name__}")
        else:
            profile["unavailable_sources"].append("Official website: unknown")

        if channel_id:
            try:
                profile["videos"] = news_feed_service.channel_videos(channel_id, client=self.client)
                profile["sources"].append({"title": "YouTube channel", "url": f"https://www.youtube.com/channel/{channel_id}"})
            except Exception as error:
                profile["unavailable_sources"].append(f"YouTube feed: {type(error).__name__}")

        filled = sum(bool(profile[key]) for key in ("summary", "faculties", "official_pages", "news", "gallery"))
        profile["status"] = "ready" if filled >= 4 else "partial" if filled else "unavailable"
        return profile

    def get(self, university: University, refresh: bool = False) -> dict[str, Any]:
        stored = university.profile
        now = datetime.now(UTC)
        if stored is not None and not refresh:
            fetched_at = stored.fetched_at if stored.fetched_at.tzinfo else stored.fetched_at.replace(tzinfo=UTC)
            if now - fetched_at < PROFILE_TTL:
                return {**stored.payload, "fetched_at": stored.fetched_at}
        payload = self.collect(university)
        serialisable = {**payload, "tuition_mentions": [{**item, "amount": str(item["amount"])} for item in payload["tuition_mentions"]],
                        "news": _dates_to_text(payload["news"]), "videos": _dates_to_text(payload["videos"])}
        if stored is None:
            stored = UniversityProfile(university_id=university.id, status=payload["status"], payload=serialisable, fetched_at=now)
            self.db.add(stored)
        else:
            stored.status, stored.payload, stored.fetched_at = payload["status"], serialisable, now
        if payload.get("website") and not university.website:
            university.website = payload["website"]
        self.db.commit()
        return {**serialisable, "fetched_at": now}


def _dates_to_text(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**item, "published_at": item["published_at"].isoformat() if isinstance(item.get("published_at"), datetime) else item.get("published_at")}
            for item in items]

