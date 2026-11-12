"""Hand-calculated reference cases for the deterministic projection engine.

Every expected number below was worked out by hand (see the comment per case),
so a regression in the engine's arithmetic shows up as a concrete mismatch.
"""

from decimal import Decimal

import pytest

from app.schemas import SimulationProjectionRequest
from app.services.simulation_projection_service import DeterministicProjectionEngine


def _run(*, years, tuition, salary, horizon, baseline="0", growth="0", baseline_growth="0",
         foregone="100", salary_range=None, **extra):
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
        **{key: Decimal(value) if isinstance(value, str) else value for key, value in extra.items()},
    )
    if salary_range is not None:
        salary_range = tuple(Decimal(value) for value in salary_range)
    return DeterministicProjectionEngine.calculate(assumptions, payload, salary_range)


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
    # v5: today's 40 000 grows through the 1 study year, so graduation-year salary is 44 000.
    # y1: 44 000 - 35 000 = 9 000 (cum 9 000); y2: 48 400 - 35 000 = 13 400 (cum 22 400)
    # -> remaining 11 000 * 12 / 13 400 = 9.85 -> 10 months -> 22; y3: 53 240 - 35 000 = 18 240.
    result = _run(years="1", tuition="20000", salary="40000", baseline="35000",
                  growth="10", foregone="0", horizon=3)
    assert result["opportunity_cost"] == Decimal("0.00")
    assert result["payback_months"] == 22
    assert result["cumulative_incremental_earnings"] == Decimal("40640.00")
    assert result["roi_percent"] == Decimal("103.20")


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


def test_growth_compounds_from_year_one_salary():
    # v5: salary in year t = start * (1 + g)^(S + t - 1); S = 1: 52 500, 55 125, 57 881.25.
    result = _run(years="1", tuition="1000", salary="50000", growth="5", horizon=3)
    assert [point["target_salary"] for point in result["salary_trajectory"]] == [
        "52500.00", "55125.00", "57881.25",
    ]


def test_scenarios_use_snapshot_min_median_max():
    # I = 10 000 * 2 = 20 000, no baseline, 5 years.
    # pessimistic 30 000: cum 150 000, ROI 650 %, payback 20 000 / 2 500 = 8 months.
    # base 40 000: cum 200 000, ROI 900 %, payback 20 000 / 3 333.33 = 6 months.
    # optimistic 60 000: cum 300 000, ROI 1 400 %, payback 20 000 / 5 000 = 4 months.
    result = _run(years="2", tuition="10000", salary="40000", horizon=5,
                  salary_range=("30000", "60000"))
    outcomes = {item["scenario"]: item for item in result["scenario_outcomes"]}
    assert list(outcomes) == ["pessimistic", "base", "optimistic"]
    assert outcomes["pessimistic"]["start_salary"] == "30000.00"
    assert outcomes["pessimistic"]["roi_percent"] == "650.00"
    assert outcomes["pessimistic"]["payback_months"] == 8
    assert outcomes["base"]["roi_percent"] == "900.00"
    assert outcomes["base"]["payback_months"] == 6
    assert outcomes["optimistic"]["cumulative_incremental_earnings"] == "300000.00"
    assert outcomes["optimistic"]["roi_percent"] == "1400.00"
    assert outcomes["optimistic"]["payback_months"] == 4
    # The headline numbers stay the base (median) scenario.
    assert result["roi_percent"] == Decimal("900.00")


def test_pessimistic_scenario_can_miss_break_even():
    # Baseline 35 000 at 0 % foregone: pessimistic start 30 000 loses money every year.
    result = _run(years="1", tuition="10000", salary="45000", baseline="35000", foregone="0",
                  horizon=3, salary_range=("30000", "50000"))
    pessimistic = result["scenario_outcomes"][0]
    assert pessimistic["break_even_reached"] is False
    assert pessimistic["payback_months"] is None
    assert pessimistic["roi_percent"] == "-250.00"


def test_npv_is_optional():
    result = _run(years="1", tuition="10000", salary="11000", horizon=2)
    assert result["npv"] is None
    assert result["scenario_outcomes"][0]["npv"] is None


def test_npv_discounts_after_graduation():
    # I = 10 000 at enrollment; study 1 year; +11 000 in post-graduation years 1 and 2.
    # NPV @10 % = -10 000 + 11 000 / 1.1^2 + 11 000 / 1.1^3 = -10 000 + 9 090.91 + 8 264.46 = 7 355.37.
    result = _run(years="1", tuition="10000", salary="11000", horizon=2,
                  discount_rate_percent="10")
    assert result["npv"] == Decimal("7355.37")
    assert result["scenario_outcomes"][0]["npv"] == "7355.37"


def test_zero_discount_rate_npv_equals_net_gain():
    # r = 0: NPV = cumulative - investment = 300 000 - 40 000.
    result = _run(years="4", tuition="10000", salary="60000", horizon=5, discount_rate_percent="0")
    assert result["npv"] == Decimal("260000.00")


def test_baseline_keeps_growing_during_study_v4():
    # foregone = 30 000 + 30 000 * 1.1 = 63 000 = I (no tuition).
    # After 2 study years the baseline is 30 000 * 1.1^2 = 36 300, so year 1 gains 50 000 - 36 300 = 13 700.
    # ROI = (13 700 - 63 000) / 63 000 = -78.25 %; the investment is not paid back.
    result = _run(years="2", tuition="0", salary="50000", baseline="30000", baseline_growth="10", horizon=1)
    assert result["opportunity_cost"] == Decimal("63000.00")
    assert result["salary_trajectory"][0]["baseline_salary"] == "36300.00"
    assert result["roi_percent"] == Decimal("-78.25")
    assert result["payback_months"] is None
    assert result["break_even_reached"] is False


def test_inflation_turns_growth_into_todays_money_v4():
    # 10 % nominal growth at 10 % inflation is 0 % real: 40 000 in both years.
    # I = 10 000 -> payback 10 000 * 12 / 40 000 = 3 months; ROI = (80 000 - 10 000) / 10 000 = 700 %.
    result = _run(years="1", tuition="10000", salary="40000", growth="10", inflation_percent="10", horizon=2)
    assert [point["target_salary"] for point in result["salary_trajectory"]] == ["40000.00", "40000.00"]
    assert result["payback_months"] == 3
    assert result["roi_percent"] == Decimal("700.00")
    assert "inflation_not_applied" not in result["unverified_assumptions"]


def test_job_search_and_employment_probability_v4():
    # y1: 6 months of 48 000 = 24 000; expected = 0.5 * 24 000 + 0.5 * 24 000 baseline = 24 000 -> gain 0.
    # y2: 0.5 * 48 000 + 0.5 * 24 000 = 36 000 -> gain 12 000; I = 12 000 tuition (0 % foregone).
    # Payback lands exactly at the end of year 2: 12 + 12 = 24 months; ROI = 0 %.
    result = _run(years="1", tuition="12000", salary="48000", baseline="24000", foregone="0",
                  job_search_months=6, employment_probability_percent="50", horizon=2)
    assert [point["incremental_earnings"] for point in result["salary_trajectory"]] == ["0.00", "12000.00"]
    assert result["payback_months"] == 24
    assert result["roi_percent"] == Decimal("0.00")


def test_nominal_mode_grows_both_paths_through_study():
    # v5 symmetry: no inflation, equal 10 % growth, 2 study years, start == baseline 30 000.
    # Both paths reach 36 300 at graduation, so the degree adds nothing in any year.
    result = _run(years="2", tuition="0", salary="30000", baseline="30000",
                  growth="10", baseline_growth="10", foregone="0", horizon=3)
    assert [point["incremental_earnings"] for point in result["salary_trajectory"]] == ["0.00", "0.00", "0.00"]
    assert result["salary_trajectory"][0]["target_salary"] == "36300.00"


def test_target_payback_verdict():
    # I = 40 000, +60 000/yr -> payback 8 months after graduation (see test_no_baseline_simple_payback).
    met = _run(years="4", tuition="10000", salary="60000", horizon=5, target_payback_years=1)
    assert met["target_payback_years"] == 1
    assert met["payback_within_target"] is True
    assert met["payback_target_gap_months"] == -4

    # I = 20 000 at +5 000/yr -> payback 48 months; a 3-year target is missed by 12 months.
    missed = _run(years="1", tuition="20000", salary="5000", horizon=5, target_payback_years=3)
    assert missed["payback_months"] == 48
    assert missed["payback_within_target"] is False
    assert missed["payback_target_gap_months"] == 12

    # Never paying back inside the horizon is a "no" without a gap.
    never = _run(years="1", tuition="10000", salary="30000", baseline="35000", foregone="0",
                 horizon=5, target_payback_years=4)
    assert never["payback_within_target"] is False
    assert never["payback_target_gap_months"] is None

    assert _run(years="1", tuition="1000", salary="50000", horizon=3)["payback_within_target"] is None


def test_target_payback_cannot_exceed_horizon():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _run(years="1", tuition="1000", salary="50000", horizon=3, target_payback_years=4)
