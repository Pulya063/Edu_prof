from unittest.mock import MagicMock

import httpx
from sqlalchemy import select

from app.core.database import db
from app.models import User
from app.services.tuition_ingestion_service import (
    CollegeScorecardTuitionProvider,
    TuitionIngestionService,
)


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
        "scope": "program",
        "country": "Poland",
        "university": "Warsaw University of Technology",
        "program": "Computer Science",
        "degree": "Bachelor",
        "study_mode": "full-time",
        "student_residency": "international",
        "institution_type": "public",
        "academic_year": "2026/2027",
        "snapshot_date": "2026-09-01",
        "currency": "pln",
        "annual_tuition_min": "11000.00",
        "annual_tuition": "12000.00",
        "annual_tuition_max": "13000.00",
        "mandatory_fees": "500.00",
        "sources": [
            {
                "name": "Official university fee schedule",
                "reference": "fees:2026-2027:cs",
                "url": "https://example.edu/fees/2026-2027",
                "acquired_at": "2026-09-02T00:00:00+00:00",
            }
        ],
        "acquired_at": "2026-09-02T00:00:00+00:00",
        "confidence": "high",
        "methodology_version": "tuition-normalization-v1",
    }
    payload.update(overrides)
    return payload


def test_tuition_snapshot_ingestion_and_resolution(client, app, monkeypatch):
    monkeypatch.setattr("app.core.redis_client.get_redis", lambda: _fake_redis())
    register = client.post(
        "/api/auth/register",
        json={"email": "tuition-admin@example.com", "password": "Passw0rd!"},
    )
    assert register.status_code == 201
    csrf_token = client.get_cookie("csrf_token").value
    headers = {"X-CSRF-Token": csrf_token}

    with app.app_context():
        user = db.session.execute(
            select(User).where(User.email == "tuition-admin@example.com")
        ).scalar_one()
        user.is_admin = True
        db.session.commit()
        db.session.remove()

    created = client.post("/api/tuition/snapshots", json=_snapshot_payload(), headers=headers)
    assert created.status_code == 201
    snapshot = created.get_json()
    assert snapshot["currency"] == "PLN"
    assert snapshot["annual_tuition"] == "12000.00"
    assert snapshot["mandatory_fees"] == "500.00"

    duplicate = client.post("/api/tuition/snapshots", json=_snapshot_payload(), headers=headers)
    assert duplicate.status_code == 200
    assert duplicate.get_json()["id"] == snapshot["id"]

    country_average = client.post(
        "/api/tuition/snapshots",
        json=_snapshot_payload(
            scope="country_average",
            university=None,
            program=None,
            degree=None,
            study_mode=None,
            institution_type=None,
            annual_tuition_min="8000.00",
            annual_tuition="10000.00",
            annual_tuition_max="14000.00",
        ),
        headers=headers,
    )
    assert country_average.status_code == 201

    resolved = client.post(
        "/api/tuition/snapshots/resolve",
        json={
            "university": "Warsaw University of Technology",
            "program": "Computer Science",
            "country": "Poland",
            "degree": "Bachelor",
            "study_mode": "full-time",
            "student_residency": "international",
            "institution_type": "public",
            "currency": "PLN",
            "as_of_date": "2026-10-02",
            "max_age_days": 365,
            "minimum_confidence": "high",
        },
        headers=headers,
    )
    assert resolved.status_code == 200
    assert resolved.get_json()["id"] == snapshot["id"]

    scenario = client.post(
        "/api/simulations",
        json={
            "name": "Verified tuition path",
            "assumptions": {
                "university": "Warsaw University of Technology",
                "specialization": "Computer Science",
                "country": "Poland",
                "degree": "Bachelor",
                "currency": "PLN",
                "study_duration_years": "4",
                "career_target": "Backend Developer",
            },
            "tuition_snapshot_selection": {
                "university": "Warsaw University of Technology",
                "program": "Computer Science",
                "country": "Poland",
                "degree": "Bachelor",
                "study_mode": "full-time",
                "student_residency": "international",
                "institution_type": "public",
                "currency": "PLN",
                "as_of_date": "2026-10-02",
                "max_age_days": 365,
                "minimum_confidence": "high",
            },
        },
        headers=headers,
    )
    assert scenario.status_code == 201
    scenario_data = scenario.get_json()
    revision = scenario_data["revisions"][0]
    assert revision["assumptions"]["annual_tuition"] == "12000.00"
    assert revision["source_snapshot_refs"] == [f"tuition_snapshot:{snapshot['id']}"]

    projection = client.post(
        f"/api/simulations/{scenario_data['id']}/revisions/1/projections",
        json={
            "annual_start_salary": "60000.00",
            "baseline_annual_salary": "0",
            "foregone_income_percent": "0",
            "horizon_years": 5,
            "evidence": [
                {
                    "metric": "target_start_salary",
                    "source_name": "Official labour statistics",
                    "source_reference": "dataset:2026-q3",
                    "acquired_at": "2026-09-30T00:00:00+00:00",
                    "country": "Poland",
                    "role": "Backend Developer",
                    "seniority": "entry",
                    "currency": "PLN",
                    "confidence": "high",
                }
            ],
        },
        headers=headers,
    )
    assert projection.status_code == 201
    projection_data = projection.get_json()
    assert projection_data["unverified_assumptions"] == []
    assert any(
        item["source_reference"] == f"tuition_snapshot:{snapshot['id']}"
        for item in projection_data["evidence"]
    )

    listed = client.get(
        "/api/tuition/snapshots?country=Poland&university=Warsaw&currency=pln"
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.get_json()] == [snapshot["id"]]

    no_fallback = client.post(
        "/api/tuition/snapshots/resolve",
        json={
            "university": "Another University",
            "program": "Economics",
            "country": "Poland",
            "student_residency": "international",
            "currency": "PLN",
            "as_of_date": "2026-10-02",
        },
        headers=headers,
    )
    assert no_fallback.status_code == 422

    fallback = client.post(
        "/api/tuition/snapshots/resolve",
        json={
            "university": "Another University",
            "program": "Economics",
            "country": "Poland",
            "student_residency": "international",
            "currency": "PLN",
            "as_of_date": "2026-10-02",
            "allow_country_fallback": True,
        },
        headers=headers,
    )
    assert fallback.status_code == 200
    assert fallback.get_json()["scope"] == "country_average"

    invalid = client.post(
        "/api/tuition/snapshots",
        json=_snapshot_payload(annual_tuition_min="15000", annual_tuition="12000"),
        headers=headers,
    )
    assert invalid.status_code == 422

    monkeypatch.setenv("COLLEGE_SCORECARD_API_KEY", "configured-test-key")
    queued_task = MagicMock(id="tuition-job-1")
    monkeypatch.setattr(
        "app.api.tuition.refresh_college_scorecard_tuition.delay",
        lambda scorecard_id: queued_task,
    )
    queued = client.post(
        "/api/tuition/snapshots/refresh/college-scorecard",
        json={"scorecard_id": 166027},
        headers=headers,
    )
    assert queued.status_code == 202
    assert queued.get_json() == {
        "job_id": "tuition-job-1",
        "provider": "college_scorecard",
        "status": "queued",
    }


def test_college_scorecard_provider_normalizes_and_deduplicates(db_session):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["id"] == "166027"
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 166027,
                        "school.name": "Massachusetts Institute of Technology",
                        "school.ownership": 2,
                        "latest.cost.tuition.in_state": 60156,
                        "latest.cost.tuition.out_of_state": 60156,
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = CollegeScorecardTuitionProvider(api_key="test-key", client=client)
    results = TuitionIngestionService(db_session, provider).refresh_college_scorecard(166027)

    assert len(results) == 2
    assert all(created for _snapshot, created in results)
    assert {snapshot.student_residency for snapshot, _created in results} == {
        "in_state",
        "out_of_state",
    }
    assert all(snapshot.currency == "USD" for snapshot, _created in results)
    assert all(snapshot.confidence == "medium" for snapshot, _created in results)

    repeated = TuitionIngestionService(db_session, provider).refresh_college_scorecard(166027)
    assert all(not created for _snapshot, created in repeated)
    client.close()
