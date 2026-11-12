"""A tuition taken from the chosen programme's published fee cites that fee document."""

from datetime import UTC, datetime
from decimal import Decimal

from app.core.database import db
from app.models import StudyProgramme, University, User
from app.schemas import SimulationCreateRequest, SimulationProjectionRequest
from app.services.simulation_projection_service import SimulationProjectionService
from app.services.simulation_service import SimulationService
from app.services.university_facts_service import load_facts

CURRENCY = {"Poland": "PLN", "Ukraine": "UAH"}


def _entry(source_kind: str) -> dict:
    return next(entry for entry in load_facts() if entry.get("fees") and entry["fees"]["source_kind"] == source_kind)


def _university_with_programme(entry: dict) -> tuple[University, StudyProgramme]:
    university = University(name=entry.get("registry_name_en") or entry["registry_name"], country=entry["country"], domains=[entry["domain"]])
    db.session.add(university)
    db.session.flush()
    row = entry["fees"]["programmes"][0]
    programme = StudyProgramme(
        university_id=university.id, country=entry["country"], name=row["programme"][:500], level=row.get("level"),
        study_mode=row.get("study_mode"), annual_fee=Decimal(str(row["amount_per_year"])), currency=entry["fees"]["currency"],
    )
    db.session.add(programme)
    db.session.commit()
    return university, programme


def _create(entry: dict, university: University, programme: StudyProgramme, annual_tuition: Decimal):
    user = User(email="fees@example.com", username="fees", password_hash="x")
    db.session.add(user)
    db.session.commit()
    country, currency = entry["country"], CURRENCY[entry["country"]]
    scenario = SimulationService(db.session).create(user.id, SimulationCreateRequest(name="Fee path", assumptions={
        "country": country, "degree": "Bachelor's degree", "currency": currency, "study_duration_years": "3", "career_target": "Lawyer",
        "university": university.name, "specialization": programme.name, "annual_tuition": str(annual_tuition),
        "existing_skills": [], "additional_education": [], "courses": [], "certifications": [], "experience_years": "0",
    }))
    request = SimulationProjectionRequest(
        annual_start_salary=Decimal("90000"), baseline_annual_salary=Decimal("0"), horizon_years=10,
        evidence=[{"metric": "target_start_salary", "source_name": "Listings", "source_reference": "test", "acquired_at": datetime.now(UTC),
                   "country": country, "role": "Lawyer", "seniority": "junior", "currency": currency, "sample_size": 40, "confidence": "medium"}],
    )
    projection, _ = SimulationProjectionService(db.session).create(user.id, scenario.id, scenario.current_revision_number, request)
    return projection


def test_official_programme_fee_is_cited_and_no_longer_unverified(app):
    with app.app_context():
        entry = _entry("official")
        university, programme = _university_with_programme(entry)
        projection = _create(entry, university, programme, programme.annual_fee)

        tuition = [item for item in projection.evidence if item["metric"] == "tuition"]
        assert len(tuition) == 1
        assert tuition[0]["source_reference"] == entry["fees"]["source_url"]
        assert tuition[0]["confidence"] == "high"
        assert "annual_tuition" not in projection.unverified_assumptions


def test_press_reported_fee_is_cited_with_medium_confidence(app):
    with app.app_context():
        entry = _entry("press")
        university, programme = _university_with_programme(entry)
        projection = _create(entry, university, programme, programme.annual_fee)

        tuition = [item for item in projection.evidence if item["metric"] == "tuition"]
        assert [item["confidence"] for item in tuition] == ["medium"]
        assert "annual_tuition" not in projection.unverified_assumptions


def test_a_typed_tuition_that_differs_from_the_fee_stays_unverified(app):
    with app.app_context():
        entry = _entry("official")
        university, programme = _university_with_programme(entry)
        projection = _create(entry, university, programme, programme.annual_fee + Decimal("1"))

        assert not [item for item in projection.evidence if item["metric"] == "tuition"]
        assert "annual_tuition" in projection.unverified_assumptions
