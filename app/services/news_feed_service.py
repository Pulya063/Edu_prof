"""Public news and video feeds (Google News RSS, YouTube channel Atom) — no API key required.

Items are copied as published (title, link, date, outlet); nothing is summarised or rewritten.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote_plus
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)

GOOGLE_NEWS_URL = "https://news.google.com/rss/search?q={query}&hl={lang}&gl={region}&ceid={region}:{lang}"
YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
CACHE_SECONDS = 6 * 60 * 60
TIMEOUT = httpx.Timeout(10.0)
# Feed language per country so local outlets are included.
COUNTRY_LOCALE = {"poland": ("pl", "PL"), "ukraine": ("uk", "UA")}


def _cache_get(key: str) -> Any | None:
    try:
        from app.core.redis_client import get_redis
        value = get_redis().get(key)
        return json.loads(value) if value else None
    except Exception:  # Cache is an optimisation; a missing Redis must not break the feature.
        return None


def _cache_set(key: str, value: Any) -> None:
    try:
        from app.core.redis_client import get_redis
        get_redis().setex(key, CACHE_SECONDS, json.dumps(value, default=str))
    except Exception:
        pass


def _fetch(url: str, client: httpx.Client | None = None) -> bytes:
    if client is not None:
        response = client.get(url)
    else:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as owned:
            response = owned.get(url)
    response.raise_for_status()
    return response.content


def news_feed_url(query: str, country: str | None = None) -> str:
    lang, region = COUNTRY_LOCALE.get((country or "").strip().casefold(), ("en", "US"))
    return GOOGLE_NEWS_URL.format(query=quote_plus(query), lang=lang, region=region)


def parse_news_rss(content: bytes, limit: int) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(content)
    items = []
    for item in root.iter("item"):
        published = item.findtext("pubDate")
        source = item.find("source")
        title = (item.findtext("title") or "").strip()
        outlet = source.text.strip() if source is not None and source.text else None
        if outlet and title.endswith(f" - {outlet}"):
            title = title[: -len(outlet) - 3]
        items.append({
            "title": title,
            "url": (item.findtext("link") or "").strip(),
            "published_at": parsedate_to_datetime(published).astimezone(UTC) if published else None,
            "source": outlet,
        })
        if len(items) >= limit:
            break
    return items


def parse_youtube_feed(content: bytes, limit: int) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(content)
    videos = []
    for entry in root.findall(f"{ATOM}entry"):
        link = entry.find(f"{ATOM}link")
        published = entry.findtext(f"{ATOM}published")
        videos.append({
            "title": (entry.findtext(f"{ATOM}title") or "").strip(),
            "url": link.get("href") if link is not None else "",
            "published_at": datetime.fromisoformat(published) if published else None,
            "source": "YouTube",
        })
        if len(videos) >= limit:
            break
    return videos


def search_news(query: str, country: str | None = None, limit: int = 6, client: httpx.Client | None = None) -> list[dict[str, Any]]:
    url = news_feed_url(query, country)
    cache_key = f"news:{url}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    items = parse_news_rss(_fetch(url, client), limit)
    _cache_set(cache_key, items)
    return items


def channel_videos(channel_id: str, limit: int = 4, client: httpx.Client | None = None) -> list[dict[str, Any]]:
    url = YOUTUBE_FEED_URL.format(channel_id=channel_id)
    cache_key = f"youtube:{channel_id}:{limit}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    videos = parse_youtube_feed(_fetch(url, client), limit)
    _cache_set(cache_key, videos)
    return videos
