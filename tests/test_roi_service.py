import pytest
from decimal import Decimal
from unittest.mock import patch

from app.schemas import TrialROIRequest
from app.services.roi_service import ROIService
from app.models import SimulationProjection, SimulationRevision, SimulationScenario, User

@pytest.fixture
def mock_market():
    with patch("app.services.market_data_service.MarketDataService.predict_career_prospects") as mock:
        mock.return_value = {
            "expected_start_salary": 48000.0,
            "average_salary": 72000.0,
            "forecast_growth_percent": 4.0,
            "demand_score": 80,
            "ai_risk_score": 20,
        }
        yield mock

def test_analyze_trial_abbreviated_result(mock_market, db_session):
    service = ROIService(db_session)
    payload = TrialROIRequest(
        university="Test Univ",
        faculty="Computer Science",
        annual_tuition=Decimal("10000.00"),
        study_years=Decimal("4.0")
    )
    
    result = service.analyze_trial(payload)
    
    assert result["education"]["specialization"] == "Computer Science"
    assert result["education"]["total_investment"]["min"] == 40000.0
    assert result["roi"]["payback_months"]["min"] > 0
    assert result["roi"]["first_year_roi_percent"]["min"] > 0

def test_trial_endpoint(mock_market, client):
    response = client.post(
        "/api/roi/trial",
        json={
            "university": "Test University",
            "faculty": "Computer Science",
            "annual_tuition": "10000.00",
            "study_years": "4"
        },
    )
    assert response.status_code == 200
    assert response.json["education"]["total_investment"]["min"] == 40000.0


@pytest.mark.parametrize("route,method", [
    ("/api/roi/analyze", "POST"),
    ("/api/roi/trash", "GET"),
    ("/api/roi/1", "DELETE"),
    ("/api/roi/1/restore", "POST"),
])
def test_removed_legacy_routes(client, route, method):
    assert client.open(route, method=method).status_code == 404


def test_projection_history_stays_owner_scoped(db_session):
    owner = User(username="history-owner", email="history-owner@example.com", password_hash="unused")
    other = User(username="history-other", email="history-other@example.com", password_hash="unused")
    db_session.add_all([owner, other])
    db_session.flush()
    for user in (owner, other):
        scenario = SimulationScenario(
            user_id=user.id,
            name="Historical university",
            target_role="Computer Science",
            country="Poland",
            currency="PLN",
            current_revision_number=1,
        )
        revision = SimulationRevision(
            revision_number=1,
            assumptions={
                "university": "Historical university",
                "career_target": "Computer Science",
                "degree": "BSc",
                "country": "Poland",
                "study_duration_years": "3",
            },
            methodology_version="scenario-input-v1",
            source_snapshot_refs=[],
        )
        scenario.revisions = [revision]
        revision.projections = [SimulationProjection(
            methodology_version="scenario-projection-v2",
            input_fingerprint=f"{user.id:064d}",
            currency="PLN",
            salary_basis="gross_annual",
            total_direct_cost=10000,
            opportunity_cost=0,
            total_investment=10000,
            estimated_start_salary=40000,
            payback_months=12,
            payback_from_enrollment_months=48,
            break_even_reached=True,
            horizon_years=5,
            cumulative_incremental_earnings=20000,
            roi_percent=20,
        )]
        db_session.add(scenario)
    db_session.commit()

    history = ROIService(db_session).get_full_history(owner)
    assert len(history) == 1
    assert history[0]["source"] == "simulation_projection"
    assert history[0]["university"] == "Historical university"
    assert history[0]["total_investment_min"] == 10000
