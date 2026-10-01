from unittest.mock import MagicMock

from sqlalchemy import select, update

from app.core.database import db
from app.models import User


def _fake_redis():
    store = {}
    client = MagicMock()
    client.setex.side_effect = lambda key, ttl, value: store.__setitem__(key, value)
    client.get.side_effect = store.get
    client.getdel.side_effect = lambda key: store.pop(key, None)
    client.delete.side_effect = lambda key: store.pop(key, None)
    return client


def _snapshot_payload(**overrides):
    payload = {
        "role": "Backend Developer",
        "country": "Poland",
        "seniority": "entry",
        "snapshot_date": "2026-09-30",
        "currency": "pln",
        "salary_min": "48000.00",
        "median_salary": "60000.00",
        "salary_max": "72000.00",
        "vacancy_count": 412,
        "demand_index": "74.50",
        "sources": [
            {
                "name": "Official labour statistics",
                "reference": "dataset:2026-q3",
                "url": "https://example.gov/market/2026-q3",
                "acquired_at": "2026-09-30T00:00:00+00:00",
            }
        ],
        "acquired_at": "2026-09-30T00:00:00+00:00",
        "sample_size": 412,
        "confidence": "high",
        "methodology_version": "market-normalization-v1",
    }
    payload.update(overrides)
    return payload


def _scenario_payload():
    return {
        "name": "Poland backend path",
        "assumptions": {
            "university": "Warsaw University of Technology",
            "specialization": "Computer Science",
            "country": "Poland",
            "degree": "Bachelor",
            "currency": "PLN",
            "annual_tuition": "12000.00",
            "study_duration_years": "4.0",
            "career_target": "Backend Developer",
            "existing_skills": ["Python"],
        },
    }


def test_admin_snapshot_ingestion_and_projection_reference(client, app, monkeypatch):
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: _fake_redis())
    register = client.post(
        "/api/auth/register",
        json={"email": "market-admin@example.com", "password": "Passw0rd!"},
    )
    assert register.status_code == 201
    csrf_token = client.get_cookie("csrf_token").value
    headers = {"X-CSRF-Token": csrf_token}

    with app.app_context():
        user = db.session.execute(
            select(User).where(User.email == "market-admin@example.com")
        ).scalar_one()
        user.is_admin = True
        db.session.commit()
        db.session.remove()

    created = client.post("/api/market/snapshots", json=_snapshot_payload(), headers=headers)
    assert created.status_code == 201
    snapshot = created.get_json()
    assert snapshot["currency"] == "PLN"
    assert snapshot["median_salary"] == "60000.00"
    assert snapshot["confidence"] == "high"

    duplicate = client.post("/api/market/snapshots", json=_snapshot_payload(), headers=headers)
    assert duplicate.status_code == 200
    assert duplicate.get_json()["id"] == snapshot["id"]

    listed = client.get("/api/market/snapshots?country=Poland&role=Backend")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.get_json()] == [snapshot["id"]]

    scenario_response = client.post(
        "/api/simulations", json=_scenario_payload(), headers=headers
    )
    assert scenario_response.status_code == 201
    scenario = scenario_response.get_json()

    projection = client.post(
        f"/api/simulations/{scenario['id']}/revisions/1/projections",
        json={
            "market_snapshot_id": snapshot["id"],
            "baseline_annual_salary": "0",
            "foregone_income_percent": "0",
            "horizon_years": 5,
        },
        headers=headers,
    )
    assert projection.status_code == 201
    forecast = projection.get_json()
    assert forecast["estimated_start_salary"] == "60000.00"
    assert forecast["payback_months"] == 10
    assert forecast["source_snapshot_refs"] == [str(snapshot["id"])]
    assert forecast["evidence"][0]["source_reference"] == f"market_snapshot:{snapshot['id']}"

    newer_payload = _snapshot_payload(
        snapshot_date="2026-10-01",
        median_salary="66000.00",
        salary_max="78000.00",
        acquired_at="2026-10-01T00:00:00+00:00",
        sources=[
            {
                "name": "Official labour statistics",
                "reference": "dataset:2026-q4",
                "url": "https://example.gov/market/2026-q4",
                "acquired_at": "2026-10-01T00:00:00+00:00",
            }
        ],
    )
    newer = client.post("/api/market/snapshots", json=newer_payload, headers=headers)
    assert newer.status_code == 201
    newer_snapshot = newer.get_json()

    resolved = client.post(
        f"/api/simulations/{scenario['id']}/revisions/1/projections",
        json={
            "market_snapshot_selection": {
                "seniority": "entry",
                "as_of_date": "2026-10-01",
                "max_age_days": 30,
                "minimum_confidence": "high",
            },
            "baseline_annual_salary": "0",
            "foregone_income_percent": "0",
            "horizon_years": 5,
        },
        headers=headers,
    )
    assert resolved.status_code == 201
    resolved_forecast = resolved.get_json()
    assert resolved_forecast["estimated_start_salary"] == "66000.00"
    assert resolved_forecast["source_snapshot_refs"] == [str(newer_snapshot["id"])]

    explainability = client.get(
        f"/api/simulations/{scenario['id']}/revisions/1/projections/"
        f"{resolved_forecast['id']}/explainability"
    )
    assert explainability.status_code == 200
    trust = explainability.get_json()
    assert trust["calculation_type"] == "deterministic"
    assert trust["ai_generated"] is False
    assert trust["salary_source_kind"] == "market_snapshot"
    assert trust["selected_salary_metric"] == "median_salary"
    assert trust["source_integrity"] == "complete"
    assert trust["source_snapshots"][0]["snapshot"]["id"] == newer_snapshot["id"]
    assert trust["source_snapshots"][0]["selected_value"] == "66000.00"
    assert trust["source_snapshots"][0]["snapshot"]["sources"][0]["url"] == (
        "https://example.gov/market/2026-q4"
    )

    no_match = client.post(
        f"/api/simulations/{scenario['id']}/revisions/1/projections",
        json={
            "market_snapshot_selection": {
                "seniority": "senior",
                "as_of_date": "2026-10-01",
            },
            "baseline_annual_salary": "0",
        },
        headers=headers,
    )
    assert no_match.status_code == 422

    wrong_role = client.post(
        "/api/market/snapshots",
        json=_snapshot_payload(role="Data Analyst"),
        headers=headers,
    )
    assert wrong_role.status_code == 201
    mismatched = client.post(
        f"/api/simulations/{scenario['id']}/revisions/1/projections",
        json={
            "market_snapshot_id": wrong_role.get_json()["id"],
            "baseline_annual_salary": "0",
        },
        headers=headers,
    )
    assert mismatched.status_code == 422

    with app.app_context():
        db.session.execute(
            update(User)
            .where(User.email == "market-admin@example.com")
            .values(is_admin=False)
        )
        db.session.commit()
        db.session.remove()
    db.session.remove()

    denied = client.post("/api/market/snapshots", json=_snapshot_payload(), headers=headers)
    assert denied.status_code == 403
