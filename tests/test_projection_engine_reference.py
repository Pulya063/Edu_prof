"""Hand-calculated reference cases for the deterministic projection engine.

Every expected number below was worked out by hand (see the comment per case),
so a regression in the engine's arithmetic shows up as a concrete mismatch.
"""

from decimal import Decimal

import pytest

from app.schemas import SimulationProjectionRequest
from app.services.simulation_projection_service import DeterministicProjectionEngine


def _run(*, years, tuition, salary, horizon, baseline="0", growth="0", baseline_growth="0",
         foregone="100", **extra):
    assumptions = {
        "currency": "USD",
        "study_duration_years": years,
        "annual_tuition": tuition,
    }
    payload = SimulationProjectionRequest(
        annual_start_salary=Decimal(salary),
        baseline_annual_salary=Decimal(baseline),
        annual_salary_growth_percent=Decimal(growth),
        baseline_salary_growth_percent=Decimal(baseline_growth),
        foregone_income_percent=Decimal(foregone),
        horizon_years=horizon,
        **{key: Decimal(value) for key, value in extra.items()},
    )
    return DeterministicProjectionEngine.calculate(assumptions, payload)


def test_no_baseline_simple_payback():
    # I = 10 000 * 4 = 40 000; +60 000/yr -> 40 000 / 5 000 per month = 8 months.
    # ROI over 5 years = (300 000 - 40 000) / 40 000 = 650 %.
    result = _run(years="4", tuition="10000", salary="60000", horizon=5)
    assert result["total_investment"] == Decimal("40000.00")
    assert result["payback_months"] == 8
    assert result["payback_from_enrollment_months"] == 48 + 8
    assert result["roi_percent"] == Decimal("650.00")


def test_opportunity_cost_and_partial_year_payback():
    # direct = 5 000 * 2 = 10 000; opportunity = 30 000 * 2 = 60 000; I = 70 000.
    # incremental = 50 000 - 30 000 = 20 000/yr; after 3 yrs cum = 60 000,
    # remaining 10 000 / (20 000 / 12) = 6 months -> 42 months.
    # ROI over 10 years = (200 000 - 70 000) / 70 000 = 185.714... %.
    result = _run(years="2", tuition="5000", salary="50000", baseline="30000", horizon=10)
    assert result["opportunity_cost"] == Decimal("60000.00")
    assert result["total_investment"] == Decimal("70000.00")
    assert result["payback_months"] == 42
    assert result["roi_percent"] == Decimal("185.71")


def test_salary_growth_payback():
    # direct 20 000; baseline 35 000 at 0 % foregone -> opportunity 0; I = 20 000.
    # y1: 40 000 - 35 000 = 5 000 (cum 5 000); y2: 44 000 - 35 000 = 9 000 (cum 14 000);
    # y3: 48 400 - 35 000 = 13 400 -> remaining 6 000 / 1 116.67 = 5.37 -> 6 months -> 30.
    result = _run(years="1", tuition="20000", salary="40000", baseline="35000",
                  growth="10", foregone="0", horizon=3)
    assert result["opportunity_cost"] == Decimal("0.00")
    assert result["payback_months"] == 30
    assert result["cumulative_incremental_earnings"] == Decimal("27400.00")
    assert result["roi_percent"] == Decimal("37.00")


def test_never_breaks_even_when_target_salary_is_below_baseline():
    # Every year loses 5 000: cum after 5 years = -25 000; I = 10 000.
    # ROI = (-25 000 - 10 000) / 10 000 = -350 %.
    result = _run(years="1", tuition="10000", salary="30000", baseline="35000",
                  foregone="0", horizon=5)
    assert result["payback_months"] is None
    assert result["break_even_reached"] is False
    assert result["roi_percent"] == Decimal("-350.00")


def test_grants_cover_all_costs():
    # 8 000 tuition - 10 000 grants -> net direct 0 (never negative); no baseline -> I = 0.
    result = _run(years="1", tuition="8000", salary="40000", horizon=3,
                  scholarships_and_grants="10000")
    assert result["total_direct_cost"] == Decimal("0.00")
    assert result["total_investment"] == Decimal("0.00")
    assert result["payback_months"] == 0
    assert result["roi_percent"] is None


def test_fees_living_cost_and_study_income():
    # direct = 6 000*3 + 1 500 fees + 2 000 courses + 3 000 living - 4 000 grants = 20 500.
    # opportunity = 24 000 * 3 * 50 % - 9 000 earned while studying = 27 000. I = 47 500.
    result = _run(years="3", tuition="6000", salary="45000", baseline="24000", foregone="50",
                  horizon=10, mandatory_fees="1500", additional_education_cost="2000",
                  incremental_living_cost="3000", scholarships_and_grants="4000",
                  employment_income_during_study="9000")
    assert result["total_direct_cost"] == Decimal("20500.00")
    assert result["opportunity_cost"] == Decimal("27000.00")
    assert result["total_investment"] == Decimal("47500.00")
    # 21 000/yr incremental: cum y2 = 42 000, remaining 5 500 / 1 750 = 3.14 -> 4 -> 28 months.
    assert result["payback_months"] == 28


@pytest.mark.parametrize("years, expected_study_months", [("1.5", 18), ("3.25", 39)])
def test_fractional_study_duration_rounds_study_months_up(years, expected_study_months):
    result = _run(years=years, tuition="1200", salary="24000", horizon=2)
    assert result["payback_from_enrollment_months"] == expected_study_months + result["payback_months"]
