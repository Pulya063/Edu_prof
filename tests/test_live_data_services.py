"""Offline tests for the live data services: parsing and arithmetic only, no network."""

from datetime import UTC, date, datetime, timezone
from decimal import Decimal

from app.models import EconomicIndicator, University
from app.services.economic_data_service import EconomicDataService
from app.services.market_ingestion_service import MarketIngestionService, SalarySample, parse_salary_range
from app.services.news_feed_service import parse_news_rss, parse_youtube_feed
from app.services.university_catalog_service import DIRECTORY_SOURCE, UniversityCatalogService
from app.services.university_profile_service import classify_links, keyword_blocks, parse_page, tuition_mentions


def test_parse_salary_range_midpoint_and_hourly_rejected():
    assert parse_salary_range("9 000–11 985 zł brutto / mies.") == Decimal("10492.5")
    assert parse_salary_range("50&#8239;000&thinsp;–&thinsp;120&#8239;000&nbsp;грн") == Decimal("85000")
    assert parse_salary_range("20000₴ за місяць") == Decimal("20000")
    assert parse_salary_range("80–120 zł / godz.") is None


def test_snapshot_payload_uses_quartiles_times_twelve():
    # Monthly 1 000 … 9 000: inclusive quartiles 3 000 / 5 000 / 7 000 -> annual 36 000 / 60 000 / 84 000.
    sample = SalarySample(monthly=[Decimal(value) for value in range(1000, 10000, 1000)],
                          sources=[{"name": "Test", "reference": "test:1", "url": "https://example.org"}], vacancy_count=9)
    payload = MarketIngestionService.build_payload("Lawyer", "Poland", "PLN", sample)
    assert (payload.salary_min, payload.median_salary, payload.salary_max) == (Decimal("36000.00"), Decimal("60000.00"), Decimal("84000.00"))
    assert payload.confidence == "low" and payload.sample_size == 9 and payload.seniority == "junior"


def test_economic_profile_median_and_devaluation(db_session):
    now = datetime.now(UTC)
    common = {"country": "Ukraine", "source_name": "test", "source_url": "https://example.org", "acquired_at": now}
    for year, value in zip(range(2019, 2026), ["4", "5", "10", "26", "5", "12", "13"]):
        db_session.add(EconomicIndicator(indicator="cpi_inflation", period=date(year, 12, 31), value=Decimal(value), unit="percent", **common))
    # 30 -> 48.4 UAH per EUR over exactly 5 years (1826 days): (48.4 / 30)^(1/4.9993) - 1 ≈ 10.04 % a year.
    db_session.add(EconomicIndicator(indicator="fx_rate", period=date(2021, 1, 2), value=Decimal("30"), unit="UAH per EUR", **common))
    db_session.add(EconomicIndicator(indicator="fx_rate", period=date(2026, 1, 2), value=Decimal("48.4"), unit="UAH per EUR", **common))
    db_session.add(EconomicIndicator(indicator="median_vacancy_wage", period=date(2026, 11, 4), value=Decimal("15000"), unit="UAH per month", **common))
    db_session.commit()

    profile = EconomicDataService(db_session).profile("ukraine")
    # Last five CPI values 10, 26, 5, 12, 13 -> median 12.
    assert profile["suggested_inflation_percent"] == Decimal("12.00")
    assert profile["inflation_window"] == "2021–2025"
    assert profile["latest_inflation_percent"] == Decimal("13.00")
    assert profile["devaluation_vs_eur_percent"] == Decimal("10.04")
    assert profile["baseline_monthly_wage"] == Decimal("15000.00")
    assert profile["baseline_wage_kind"] == "median_vacancy_wage"


def test_university_directory_import_is_idempotent(db_session):
    rows = [
        {"name": "Warsaw  University of Technology", "country": "Poland", "domains": ["pw.edu.pl"], "web_pages": ["http://www.pw.edu.pl/"]},
        {"name": "Lviv Polytechnic National University", "country": "Ukraine", "domains": ["lp.edu.ua"], "web_pages": ["http://www.lp.edu.ua/"]},
        {"name": "MIT", "country": "United States", "domains": ["mit.edu"], "web_pages": ["https://mit.edu"]},
    ]
    service = UniversityCatalogService(db_session)
    assert service.import_countries(rows=rows) == 2
    assert service.import_countries(rows=rows) == 0
    stored = db_session.query(University).filter(University.source == DIRECTORY_SOURCE).order_by(University.name).all()
    assert [(item.name, item.domains) for item in stored] == [
        ("Lviv Polytechnic National University", ["lp.edu.ua"]),
        ("Warsaw University of Technology", ["pw.edu.pl"]),
    ]


def test_official_site_links_prefer_sections_over_articles():
    page = parse_page("""
      <a href="/">Strona główna</a>
      <a href="/aktualnosci/stypendia-2026">Stypendia dla najlepszych</a>
      <a href="/studia/stypendia">Stypendia</a>
      <a href="/praca/kandydaci-do-pracy">Kandydaci do pracy</a>
      <a href="https://rekrutacja.pw.edu.pl/">Rekrutacja</a>
      <a href="https://other.example.org/sport">Sport</a>
    """)
    found = {(item["kind"], item["url"]) for item in classify_links("https://www.pw.edu.pl/", page.links)}
    assert ("scholarships", "https://www.pw.edu.pl/studia/stypendia") in found
    assert ("admissions", "https://rekrutacja.pw.edu.pl/") in found
    assert not any("kandydaci-do-pracy" in url or "other.example.org" in url for _, url in found)
    # A news article may be listed as news, never as the scholarships section.
    assert not any(kind != "news" and "aktualnosci" in url for kind, url in found)


def test_tuition_amounts_and_documents_are_copied_not_invented():
    page = parse_page("""
      <p>Opłata za rok studiów wynosi 12 000 zł dla cudzoziemców.</p>
      <li>Za semestr: 3 500 EUR</li>
      <li>Kopia świadectwa dojrzałości i paszport</li>
      <li>Kontakt</li>
    """)
    mentions = tuition_mentions(page.blocks, "https://example.edu/fees")
    assert [(item["amount"], item["currency"], item["period"]) for item in mentions] == [
        (Decimal("12000"), "PLN", "year"), (Decimal("3500"), "EUR", "semester"),
    ]
    documents = keyword_blocks(page.blocks, ("świadectw", "paszport"), "https://example.edu/apply", 5, min_hits=2)
    assert [item["text"] for item in documents] == ["Kopia świadectwa dojrzałości i paszport"]


def test_news_and_youtube_feeds_are_parsed_verbatim():
    rss = b"""<rss><channel><item><title>Politechnika otwiera nowy wydzial - Gazeta</title>
      <link>https://news.example/a</link><pubDate>Tue, 03 Nov 2026 10:00:00 GMT</pubDate>
      <source url="https://gazeta.example">Gazeta</source></item></channel></rss>"""
    item = parse_news_rss(rss, 5)[0]
    assert item["title"] == "Politechnika otwiera nowy wydzial" and item["source"] == "Gazeta"
    assert item["published_at"].year == 2026

    atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Open day</title>
      <link rel="alternate" href="https://www.youtube.com/watch?v=x"/><published>2026-10-01T08:00:00+00:00</published></entry></feed>"""
    assert parse_youtube_feed(atom, 3)[0]["url"] == "https://www.youtube.com/watch?v=x"
