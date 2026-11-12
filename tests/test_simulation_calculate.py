"""POST /api/simulations/calculate: one scenario with a forecast, or nothing at all.

Also covers the salary lookup for a role with no stored data, including its failure paths.
"""
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest

from app.core.database import db
from app.core.security import create_jwt_access_token
from app.models import MarketSnapshot, SimulationProjection, SimulationScenario, User
from app.services.market_ingestion_service import MarketProviderError

CSRF = "test-csrf-token"
FETCH_CUSTOM = "app.services.market_ingestion_service.MarketIngestionService.fetch_custom"
REFRESH_CATALOG = "app.services.official_wage_service.refresh_salary_snapshot"


def _sign_in(client) -> int:
    user = User(email="calc@example.com", username="calc", password_hash="x")
    db.session.add(user)
    db.session.commit()
    client.set_cookie("access_token", create_jwt_access_token(subject=str(user.id)))
    client.set_cookie("csrf_token", CSRF)
    return user.id


def _body(role="Kucharz", **projection):
    now = datetime.now(UTC).isoformat()
    return {
        "scenario": {
            "name": f"{role} path",
            "assumptions": {
                "country": "Poland", "degree": "Bachelor's degree", "currency": "PLN", "study_duration_years": "3.5", "career_target": role,
                "annual_tuition": "10000", "existing_skills": [], "additional_education": [], "courses": [], "certifications": [], "experience_years": "0",
            },
        },
        "projection": {
            "market_snapshot_selection": {"seniority": "junior", "max_age_days": 365, "minimum_confidence": "medium"},
            "baseline_annual_salary": "0",
            "horizon_years": 10,
            "auto_assumptions": True,
            "evidence": [{"metric": "tuition", "source_name": "User-provided tuition estimate", "source_reference": "user-provided:scenario-form", "acquired_at": now,
                          "country": "Poland", "role": role, "seniority": "junior", "currency": "PLN", "confidence": "low"}],
            **projection,
        },
    }


def _store_snapshot(role):
    db.session.add(MarketSnapshot(
        role=role, country="Poland", seniority="junior", snapshot_date=date.today(), currency="PLN", salary_basis="gross_annual",
        salary_min=Decimal("60000"), median_salary=Decimal("72000"), salary_max=Decimal("90000"), vacancy_count=12,
        sources=[{"name": "test", "reference": "test:1"}], acquired_at=datetime.now(UTC), sample_size=12, confidence="low",
        methodology_version="listing-quartiles-v2", validation_status="validated", fingerprint="c" * 64,
    ))
    db.session.commit()


def _post(client, body):
    return client.post("/api/simulations/calculate", json=body, headers={"X-CSRF-Token": CSRF})


def test_success_keeps_the_scenario_and_its_forecast(client):
    user_id = _sign_in(client)
    with patch(FETCH_CUSTOM, side_effect=lambda *_: _store_snapshot("Kucharz")) as fetch:
        response = _post(client, _body())
    assert response.status_code == 201, response.get_json()
    fetch.assert_called_once_with("Kucharz", "Poland", "PLN")
    scenario = db.session.get(SimulationScenario, response.get_json()["id"])
    assert scenario.user_id == user_id
    assert db.session.query(SimulationProjection).count() == 1


@pytest.mark.parametrize("error", [MarketProviderError("too few listings"), httpx.ConnectError("offline")], ids=["too-few-salaries", "site-offline"])
def test_no_salary_data_gives_a_clear_422_and_leaves_no_scenario(client, error):
    _sign_in(client)
    with patch(FETCH_CUSTOM, side_effect=error):
        response = _post(client, _body())
    assert response.status_code == 422
    assert "could not find enough published salaries for 'Kucharz'" in response.get_json()["detail"]
    assert db.session.query(SimulationScenario).count() == 0


def test_lookup_that_stores_nothing_is_also_a_422(client):
    _sign_in(client)
    with patch(FETCH_CUSTOM, return_value=None):
        response = _post(client, _body())
    assert response.status_code == 422
    assert db.session.query(SimulationScenario).count() == 0


def test_listed_role_uses_the_catalog_lookup(client):
    _sign_in(client)
    with patch(REFRESH_CATALOG, side_effect=lambda *_: _store_snapshot("Lawyer")) as refresh, patch(FETCH_CUSTOM) as fetch:
        response = _post(client, _body(role="lawyer"))
    assert response.status_code == 201, response.get_json()
    assert refresh.call_args.args[1:] == ("lawyer", "Poland", "PLN")
    fetch.assert_not_called()


def test_unexpected_failure_also_leaves_no_scenario(client):
    _sign_in(client)
    with patch(FETCH_CUSTOM, side_effect=RuntimeError("boom")), pytest.raises(RuntimeError):
        _post(client, _body())
    assert db.session.query(SimulationScenario).count() == 0


def test_invalid_input_keeps_field_paths_and_creates_nothing(client):
    _sign_in(client)
    body = _body(horizon_years=0)
    response = _post(client, body)
    assert response.status_code == 422
    assert "horizon_years" in str(response.get_json())
    assert "projection.horizon_years" not in str(response.get_json())
    assert db.session.query(SimulationScenario).count() == 0


def test_requires_sign_in(client):
    response = client.post("/api/simulations/calculate", json=_body())
    assert response.status_code == 401
    assert response.get_json()["detail"] == "Sign in to continue"
