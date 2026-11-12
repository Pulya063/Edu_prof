from unittest.mock import MagicMock
from decimal import Decimal

from app.schemas import SimulationProjectionRequest
from app.services.simulation_projection_service import DeterministicProjectionEngine


def _assumptions(**overrides):
    values = {
        "university": "Warsaw University of Technology",
        "specialization": "Computer Science",
        "country": "Poland",
        "degree": "Bachelor",
        "currency": "pln",
        "annual_tuition": "12000.00",
        "study_duration_years": "4.0",
        "career_target": "Backend Developer",
        "existing_skills": ["Python"],
        "additional_education": [],
        "courses": [],
        "certifications": [],
        "experience_years": "0.0",
    }
    values.update(overrides)
    return values


def _evidence(metric, role="Backend Developer"):
    return {
        "metric": metric,
        "source_name": "Official labour statistics",
        "source_reference": "dataset:2026-q3",
        "acquired_at": "2026-09-30T00:00:00+00:00",
        "country": "Poland",
        "role": role,
        "seniority": "entry",
        "currency": "PLN",
        "sample_size": 412,
        "confidence": "high",
    }


def _projection_payload():
    return {
        "annual_start_salary": "50000.00",
        "baseline_annual_salary": "20000.00",
        "annual_salary_growth_percent": "0",
        "baseline_salary_growth_percent": "0",
        "foregone_income_percent": "50",
        "additional_education_cost": "2000.00",
        "incremental_living_cost": "4000.00",
        "horizon_years": 5,
        "evidence": [
            _evidence("target_start_salary"),
            _evidence("baseline_salary", role="Current employment"),
        ],
    }


def test_deterministic_projection_uses_incremental_earnings():
    payload = SimulationProjectionRequest.model_validate(_projection_payload())
    result = DeterministicProjectionEngine.calculate(_assumptions(), payload)

    assert result["total_direct_cost"] == 54000
    assert result["opportunity_cost"] == 40000
    assert result["total_investment"] == 94000
    assert result["payback_months"] == 38
    assert result["payback_from_enrollment_months"] == 86
    assert result["cumulative_incremental_earnings"] == 150000
    assert result["roi_percent"] == Decimal("59.57")


def test_detailed_projection_offsets_optional_study_income_and_keeps_downside_years():
    payload_data = _projection_payload()
    payload_data.update(
        {
            "annual_start_salary": "15000.00",
            "baseline_annual_salary": "20000.00",
            "mandatory_fees": "3000.00",
            "scholarships_and_grants": "10000.00",
            "employment_income_during_study": "12000.00",
        }
    )
    payload = SimulationProjectionRequest.model_validate(payload_data)
    result = DeterministicProjectionEngine.calculate(_assumptions(), payload)

    assert result["total_direct_cost"] == 47000
    assert result["opportunity_cost"] == 28000
    assert result["total_investment"] == 75000
    assert result["cumulative_incremental_earnings"] == -25000
    assert result["payback_months"] is None
    assert result["payback_from_enrollment_months"] is None
    assert result["salary_trajectory"][0]["incremental_earnings"] == "-5000.00"


def test_simulation_scenario_revision_flow(client, monkeypatch):
    redis_store = {}
    fake_redis = MagicMock()
    fake_redis.setex.side_effect = lambda key, ttl, value: redis_store.__setitem__(key, value)
    fake_redis.get.side_effect = redis_store.get
    fake_redis.getdel.side_effect = lambda key: redis_store.pop(key, None)
    fake_redis.delete.side_effect = lambda key: redis_store.pop(key, None)
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: fake_redis)

    register = client.post(
        "/api/auth/register",
        json={"email": "scenario@example.com", "password": "Passw0rd!"},
    )
    assert register.status_code == 201
    csrf_token = client.get_cookie("csrf_token").value
    headers = {"X-CSRF-Token": csrf_token}

    created = client.post(
        "/api/simulations",
        json={"name": "Poland CS path", "assumptions": _assumptions()},
        headers=headers,
    )
    assert created.status_code == 201
    scenario = created.get_json()
    assert scenario["current_revision_number"] == 1
    assert scenario["currency"] == "PLN"
    assert len(scenario["revisions"]) == 1
    original_assumptions = scenario["revisions"][0]["assumptions"]

    revised = client.post(
        f"/api/simulations/{scenario['id']}/revisions",
        json={
            "change_note": "Added internship experience",
            "assumptions": _assumptions(experience_years="1.0", career_target="Python Developer"),
        },
        headers=headers,
    )
    assert revised.status_code == 201
    updated = revised.get_json()
    assert updated["current_revision_number"] == 2
    assert updated["target_role"] == "Python Developer"
    assert [revision["revision_number"] for revision in updated["revisions"]] == [1, 2]
    assert updated["revisions"][0]["assumptions"] == original_assumptions
    assert updated["revisions"][1]["change_note"] == "Added internship experience"

    projection = client.post(
        f"/api/simulations/{scenario['id']}/revisions/2/projections",
        json=_projection_payload(),
        headers=headers,
    )
    assert projection.status_code == 201
    forecast = projection.get_json()
    assert forecast["methodology_version"] == "scenario-projection-v5"
    # Manual salary: only the base scenario exists, and NPV stays null without a discount rate.
    assert [item["scenario"] for item in forecast["scenario_outcomes"]] == ["base"]
    assert forecast["scenario_outcomes"][0]["roi_percent"] == forecast["roi_percent"]
    assert forecast["npv"] is None
    assert forecast["payback_months"] == 38
    assert forecast["payback_from_enrollment_months"] == 86
    assert forecast["total_investment"] == 94000.00
    assert forecast["calculation_inputs"]["annual_start_salary"] == 50000.00
    assert forecast["cost_breakdown"]["tuition"] == 48000.00
    assert forecast["unverified_assumptions"] == ["annual_tuition", "inflation_not_applied"]
    assert forecast["ai_review"]["status"] == "not_configured"

    explainability = client.get(
        f"/api/simulations/{scenario['id']}/revisions/2/projections/"
        f"{forecast['id']}/explainability"
    )
    assert explainability.status_code == 200
    trust = explainability.get_json()
    assert trust["calculation_type"] == "deterministic"
    assert trust["ai_generated"] is False
    assert trust["salary_source_kind"] == "manual_evidence"
    assert trust["selected_salary_metric"] == "annual_start_salary"
    assert trust["source_snapshots"] == []
    assert trust["source_integrity"] == "complete"

    overview = client.get("/api/simulations/overview")
    assert overview.status_code == 200
    overview_data = overview.get_json()
    assert overview_data["status"] == "projected"
    assert overview_data["scenario"]["id"] == scenario["id"]
    assert overview_data["projection"]["id"] == forecast["id"]
    assert overview_data["explainability"]["calculation_type"] == "deterministic"
    recent = overview_data["recent_calculations"]
    assert [item["scenario_id"] for item in recent] == [scenario["id"]]
    assert recent[0]["projection_id"] == forecast["id"]
    assert recent[0]["revision_number"] == 2
    assert recent[0]["roi_percent"] == forecast["roi_percent"]
    assert recent[0]["payback_months"] == forecast["payback_months"]
    assert recent[0]["total_investment"] == forecast["total_investment"]

    reviewed = client.post(
        f"/api/simulations/{scenario['id']}/revisions/2/projections/"
        f"{forecast['id']}/ai-review",
        headers=headers,
    )
    assert reviewed.status_code == 200
    assert reviewed.get_json()["ai_review"]["status"] == "not_configured"

    retired = client.post("/api/roi/analyze", json={}, headers=headers)
    assert retired.status_code == 404

    duplicate = client.post(
        f"/api/simulations/{scenario['id']}/revisions/2/projections",
        json=_projection_payload(),
        headers=headers,
    )
    assert duplicate.status_code == 200
    assert duplicate.get_json()["id"] == forecast["id"]

    projections = client.get(f"/api/simulations/{scenario['id']}/revisions/2/projections")
    assert projections.status_code == 200
    assert len(projections.get_json()) == 1

    listed = client.get("/api/simulations")
    assert listed.status_code == 200
    [row] = listed.get_json()
    assert row["id"] == scenario["id"]
    # List rows carry the current revision's inputs and the stored forecast numbers, nothing else.
    assert row["projection_id"] == forecast["id"]
    assert row["roi_percent"] == forecast["roi_percent"]
    assert row["total_investment"] == forecast["total_investment"]
    assert row["payback_months"] == forecast["payback_months"]
    assert isinstance(row["study_duration_years"], float)

    invalid = client.post(
        "/api/simulations",
        json={"name": "Invalid", "assumptions": _assumptions(annual_tuition="-1")},
        headers=headers,
    )
    assert invalid.status_code == 422


def test_overview_lists_recent_calculations_without_inventing_numbers(client, monkeypatch):
    redis_store = {}
    fake_redis = MagicMock()
    fake_redis.setex.side_effect = lambda key, ttl, value: redis_store.__setitem__(key, value)
    fake_redis.get.side_effect = redis_store.get
    fake_redis.getdel.side_effect = lambda key: redis_store.pop(key, None)
    fake_redis.delete.side_effect = lambda key: redis_store.pop(key, None)
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: fake_redis)

    client.post("/api/auth/register", json={"email": "recent@example.com", "password": "Passw0rd!"})
    headers = {"X-CSRF-Token": client.get_cookie("csrf_token").value}

    empty = client.get("/api/simulations/overview").get_json()
    assert empty["status"] == "empty"
    assert empty["recent_calculations"] == []

    created = client.post(
        "/api/simulations",
        json={"name": "Draft path", "assumptions": _assumptions()},
        headers=headers,
    ).get_json()

    overview = client.get("/api/simulations/overview").get_json()
    assert overview["status"] == "scenario_only"
    [item] = overview["recent_calculations"]
    assert item["scenario_id"] == created["id"]
    assert item["projection_id"] is None
    assert item["roi_percent"] is None
    assert item["payback_months"] is None

    [row] = client.get("/api/simulations").get_json()
    assert row["degree"] == _assumptions()["degree"]
    assert row["university"] == _assumptions()["university"]
    assert row["projection_id"] is None
    assert row["total_investment"] is None
    assert row["roi_percent"] is None
