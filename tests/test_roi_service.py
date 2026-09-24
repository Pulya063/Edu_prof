import pytest
from decimal import Decimal
from unittest.mock import patch

from app.schemas import CareerAnalysisRequest, TrialROIRequest
from app.services.roi_service import ROIService
from app.models import CareerAnalysis

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

@pytest.fixture
def mock_onet():
    with patch("app.services.onet_service.OnetService.get_profession_data") as mock:
        mock.return_value = {
            "found": True,
            "demand_score": 85,
            "ai_risk_score": 15,
            "skills": ["Python", "SQL"],
            "bright_outlook": True
        }
        yield mock

@pytest.fixture
def mock_ai():
    with patch("app.services.ai_rag_service.AIRAGService.generate_qualitative_insights") as mock:
        mock.return_value = {
            "ai_risk_score": 25,
            "skills_to_learn_outside_university": ["Docker", "AWS"],
            "recommended_strategy": {
                "year_1": "Learn basics",
                "year_2": "Internship",
                "year_3": "Build portfolio",
                "final_stage": "Apply for jobs"
            },
            "biggest_risk": {
                "risk": "Burnout",
                "result": "Take breaks"
            },
            "verdict": "Good choice."
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

def test_analyze_career_full_analysis(mock_market, mock_onet, mock_ai, db_session):
    service = ROIService(db_session)
    payload = CareerAnalysisRequest(
        university="WSIiZ Rzeszow",
        degree="BSc",
        specialization_focus="Software Engineering",
        country="Poland",
        currency="USD",
        study_years=Decimal("3.5"),
        monthly_payment=Decimal("1000.00"),
        payments_per_year=10,
        additional_learning_budget_min=Decimal("0"),
        additional_learning_budget_max=Decimal("2000.00"),
        include_living_costs=False
    )
    
    result = service.analyze_career(payload)
    
    assert result["education"]["total_investment"]["min"] == 35000.00
    assert result["education"]["total_investment"]["max"] == 41200.00
    
    # Check that AI insight overrides are present
    assert result["verdict"] == "Good choice."
    assert result["biggest_risk"]["risk"] == "Burnout"
    assert result["skills_to_learn_outside_university"] == ["Docker", "AWS"]
    
    # Check if saved to DB
    analysis = db_session.query(CareerAnalysis).first()
    assert analysis is not None
    assert analysis.specialization == "Software Engineering"
    assert analysis.country == "Poland"

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

def test_analyze_endpoint_requires_auth(mock_market, mock_onet, mock_ai, client):
    response = client.post(
        "/api/roi/analyze",
        json={
            "university": "WSIiZ",
            "degree": "BSc",
            "specialization_focus": "Software Engineering",
            "monthly_payment": "1000.00",
            "payments_per_year": 12,
            "study_years": "3"
        }
    )
    assert response.status_code == 401
