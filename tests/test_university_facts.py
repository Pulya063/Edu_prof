import pytest

from app.models import University
from app.services.university_facts_service import ensure_catalogue_rows, facts_for, load_facts

ENTRIES = load_facts()


def test_top_thirty_are_present_with_addresses():
    assert len(ENTRIES) == 30
    assert {entry["country"] for entry in ENTRIES} == {"Poland", "Ukraine"}
    assert all(entry["address"]["street"] and entry["address"]["city"] and entry["address"]["source_url"] for entry in ENTRIES)


@pytest.mark.parametrize("entry", [entry for entry in ENTRIES if entry["fees"]], ids=lambda entry: entry["domain"])
def test_fee_summaries_agree_with_their_rows(entry):
    fees = entry["fees"]
    amounts = [row["amount_per_year"] for row in fees["programmes"]]
    assert fees["min_per_year"] == min(amounts) == fees["cheapest"]["amount_per_year"] and min(amounts) > 0
    assert fees["max_per_year"] == max(amounts) == fees["most_expensive"]["amount_per_year"]
    assert fees["paid_programme_count"] == len(amounts)
    assert fees["currency"] == {"Poland": "PLN", "Ukraine": "UAH"}[entry["country"]]
    assert fees["source_kind"] == {"Poland": "official", "Ukraine": "press"}[entry["country"]]
    assert fees["source_url"].startswith("https://") and fees["max_per_year"] < 400000


def test_a_directory_row_finds_facts_through_its_older_domain():
    row = University(name="Technical University of Gdansk", country="Poland", domains=["pg.gda.pl"])
    assert facts_for(row)["domain"] == "pg.edu.pl"
    assert facts_for(University(name="Other", country="Poland", domains=["example.pl"])) is None
    assert facts_for(University(name="Same domain, other country", country="Ukraine", domains=["pg.gda.pl"])) is None


def test_missing_top_universities_are_added_once(db_session):
    db_session.add(University(name="Warsaw University of Technology", country="Poland", domains=["pw.edu.pl"]))
    db_session.commit()

    assert ensure_catalogue_rows(db_session) == len(ENTRIES) - 1
    assert ensure_catalogue_rows(db_session) == 0
