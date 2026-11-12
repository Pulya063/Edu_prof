from decimal import Decimal

from app.schemas import SimulationProjectionRequest
from app.services.career_ladder_service import ladder_from_medians
from app.services.simulation_projection_service import DeterministicProjectionEngine


def test_ladder_junior_mid_senior_then_flat():
    ladder = ladder_from_medians("junior", Decimal("100"), {"mid": Decimal("150"), "senior": Decimal("220")}, 10)
    assert ladder == [Decimal("1")] * 2 + [Decimal("1.5")] * 3 + [Decimal("2.2")] * 5


def test_ladder_stops_at_missing_level():
    # No mid data: nothing is guessed, the senior figure is not used either.
    assert ladder_from_medians("junior", Decimal("100"), {"senior": Decimal("220")}, 10) == []
    assert ladder_from_medians("junior", Decimal("100"), {"mid": Decimal("130")}, 10) == [Decimal("1")] * 2 + [Decimal("1.3")] * 8


def test_ladder_never_drops_between_levels():
    ladder = ladder_from_medians("junior", Decimal("100"), {"mid": Decimal("90"), "senior": Decimal("120")}, 10)
    assert ladder[2:5] == [Decimal("1")] * 3 and ladder[5:] == [Decimal("1.2")] * 5


def test_ladder_from_mid_start():
    assert ladder_from_medians("mid", Decimal("200"), {"senior": Decimal("300")}, 6) == [Decimal("1")] * 3 + [Decimal("1.5")] * 3


def test_engine_applies_ladder_to_target_salary_only():
    payload = SimulationProjectionRequest(
        annual_start_salary=Decimal("100000"), baseline_annual_salary=Decimal("40000"), horizon_years=6,
        career_ladder=[Decimal("1"), Decimal("1"), Decimal("1.5"), Decimal("1.5"), Decimal("1.5"), Decimal("2")],
    )
    result = DeterministicProjectionEngine.calculate({"study_duration_years": 3, "annual_tuition": 0, "currency": "PLN"}, payload)
    salaries = [Decimal(point["target_salary"]) for point in result["salary_trajectory"]]
    assert salaries == [Decimal("100000.00")] * 2 + [Decimal("150000.00")] * 3 + [Decimal("200000.00")]
    assert {point["baseline_salary"] for point in result["salary_trajectory"]} == {"40000.00"}
