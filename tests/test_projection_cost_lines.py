from datetime import UTC, datetime
from decimal import Decimal

from app.core.database import db
from app.models import EconomicIndicator, MarketSnapshot, User  # noqa: F401
from app.schemas import ProjectionPreviewResponse, SimulationProjectionRequest, SimulationProjectionResponse
from app.services.projection_assumptions import job_search_months
from app.services.simulation_projection_service import SimulationProjectionService
from app.services.simulation_service import SimulationService
from app.schemas import SimulationCreateRequest


def _indicator(indicator, value, unit="percent", year=2024):
    db.session.add(EconomicIndicator(country="Poland", indicator=indicator, period=datetime(year, 12, 31, tzinfo=UTC).date(), value=Decimal(str(value)), unit=unit,
                                     source_name=f"Source of {indicator}", source_url="https://example.org/" + indicator, acquired_at=datetime.now(UTC)))


def _scenario(user_id, **assumptions):
    base = {"country": "Poland", "degree": "Bachelor's degree", "currency": "PLN", "study_duration_years": "3.5", "career_target": "Lawyer", "annual_tuition": "10000",
            "existing_skills": [], "additional_education": [], "courses": [], "certifications": [], "experience_years": "0"}
    return SimulationService(db.session).create(user_id, SimulationCreateRequest(name="Lawyer path", assumptions={**base, **assumptions}))


def _request(**extra):
    now = datetime.now(UTC)
    return SimulationProjectionRequest(
        annual_start_salary=Decimal("90000"), baseline_annual_salary=Decimal("0"), horizon_years=10, auto_assumptions=True,
        evidence=[{"metric": "target_start_salary", "source_name": "Listings", "source_reference": "test", "acquired_at": now, "country": "Poland", "role": "Lawyer",
                   "seniority": "junior", "currency": "PLN", "sample_size": 40, "confidence": "medium"}],
        **extra,
    )


def _user():
    user = User(email="costs@example.com", username="costs", password_hash="x")
    db.session.add(user); db.session.commit()
    return user


def _seed_economics():
    for year, value in ((2022, 14), (2023, 11), (2024, 4)):
        _indicator("cpi_inflation", value, year=year)
    _indicator("minimum_wage", 4000, unit="PLN")
    _indicator("graduate_unemployment", 1.5)
    db.session.commit()


def test_job_search_follows_open_vacancies():
    assert [job_search_months(n) for n in (None, 5, 12, 40, 200)] == [3, 6, 4, 3, 2]


def test_auto_calculation_fills_inputs_and_lists_every_line(app):
    with app.app_context():
        user = _user(); _seed_economics()
        scenario = _scenario(user.id)
        service = SimulationProjectionService(db.session)
        projection, created = service.create(user.id, scenario.id, scenario.current_revision_number, _request())
        assert created
        data = SimulationProjectionResponse.model_validate(projection)
        inputs = data.calculation_inputs
        assert inputs.employment_probability_percent == Decimal("98.50")
        assert inputs.job_search_months == 3
        assert inputs.discount_rate_percent == Decimal("5")
        assert inputs.inflation_percent is not None
        assert inputs.baseline_annual_salary == Decimal("48000.00")
        lines = {item.key: item for item in inputs.cost_items}
        assert lines["tuition"].amount == Decimal("35000.00")
        assert lines["housing"].per_month == Decimal("830")
        assert lines["housing"].amount == Decimal("34860.00")
        assert lines["housing"].source == "country_average"
        # Lines add up to the direct cost: nothing is hidden in a lump.
        paid = sum(item.amount for key, item in lines.items() if key in {"tuition", "mandatory_fees", "housing", "food", "other_living", "additional_training"})
        assert data.cost_breakdown.net_direct_cost == paid


def test_university_and_specialization_are_optional(app):
    with app.app_context():
        user = _user()
        scenario = _scenario(user.id)
        assumptions = scenario.revisions[-1].assumptions
        assert assumptions.get("university") is None and assumptions.get("specialization") is None


def test_switching_a_line_off_previews_without_saving_then_saves(app):
    with app.app_context():
        user = _user(); _seed_economics()
        scenario = _scenario(user.id)
        service = SimulationProjectionService(db.session)
        revision = scenario.current_revision_number
        projection, _ = service.create(user.id, scenario.id, revision, _request())
        before = projection.total_investment
        items = [item.model_copy() for item in SimulationProjectionResponse.model_validate(projection).calculation_inputs.cost_items]
        for item in items:
            if item.key == "housing":
                item.enabled = False
            if item.key == "additional_training":
                item.amount = Decimal("5000")
        preview = ProjectionPreviewResponse.model_validate(service.recalculate(user.id, scenario.id, revision, projection.id, items, save=False))
        assert preview.total_investment == before - Decimal("34860.00") + Decimal("5000")
        assert len(service.list_for_revision(user.id, scenario.id, revision)) == 1
        saved, created = service.recalculate(user.id, scenario.id, revision, projection.id, items, save=True)
        assert created and saved.total_investment == preview.total_investment
        assert len(service.list_for_revision(user.id, scenario.id, revision)) == 2


def test_switching_pay_off_removes_it_from_the_investment(app):
    with app.app_context():
        user = _user(); _seed_economics()
        scenario = _scenario(user.id)
        service = SimulationProjectionService(db.session)
        revision = scenario.current_revision_number
        projection, _ = service.create(user.id, scenario.id, revision, _request())
        items = [item.model_copy() for item in SimulationProjectionResponse.model_validate(projection).calculation_inputs.cost_items]
        for item in items:
            if item.key == "pay_given_up":
                item.enabled = False
        preview = service.recalculate(user.id, scenario.id, revision, projection.id, items, save=False)
        assert Decimal(str(preview["cost_breakdown"]["opportunity_cost"])) == 0
