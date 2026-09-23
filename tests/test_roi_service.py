import pytest
from decimal import Decimal
from unittest.mock import patch

from pydantic import ValidationError

from app.services.roi_service import ROIService
from app.schemas import ROICalculationRequest

def test_yearly_salaries(db_session):
    """Перевірка правильності розрахунку зарплат за моделлю Мінсера."""
    service = ROIService(db_session)
    start_salary = Decimal("10000.00")
    years = 3
    
    # Викликаємо метод (це private method, але тестуємо для надійності)
    salaries = service._yearly_salaries(start_salary, years)
    
    # Початкова зарплата (рік 0)
    assert salaries[0] == Decimal("10000.00")
    
    # Рік 1: +8% (10800)
    assert salaries[1] == Decimal("10800.00")
    
    # Рік 2: +8% (11664)
    assert salaries[2] == Decimal("11664.00")
    
    # Рік 3: +8% (12597.12)
    assert salaries[3] == Decimal("12597.12")
    
    assert len(salaries) == 4

def test_break_even(db_session):
    """Перевірка розрахунку місяців до повної окупності (Break-Even)."""
    service = ROIService(db_session)
    
    # Вартість навчання: 10,000. Початкова зарплата: 12,000 (тобто 1000/місяць)
    # Без урахування росту зарплати, окупність була б 10 місяців.
    # Оскільки зарплата зростає, окупність має настати швидше, але 
    # ріст відбувається щомісяця (річний відсоток / 12).
    # Для першого року ріст 8%/12 на місяць.
    # Тому окупність має бути близько 10 місяців.
    
    total_cost = Decimal("10000.00")
    starting_salary = Decimal("12000.00")
    
    months = service._break_even(total_cost, starting_salary)
    
    assert isinstance(months, int)
    assert 1 <= months <= 10 # Має бути менше або дорівнювати 10, оскільки зарплата росте.

@patch("app.services.ai_rag_service.AIRAGService.predict_career_prospects")
def test_calculate_roi_with_mocked_ai(mock_predict, db_session):
    """Перевірка основного методу розрахунку ROI з підміною AI сервісу."""
    # Імітуємо відповідь від RAG/AI
    mock_predict.return_value = {
        "expected_start_salary": 50000.0,
        "average_salary": 60000.0,
        "forecast_growth_percent": 3.0,
        "demand_score": 85,
        "ai_risk_score": 15
    }
    
    service = ROIService(db_session)
    payload = ROICalculationRequest(
        university="Test University",
        faculty="Computer Science",
        annual_tuition=Decimal("15000.00"),
    )
    
    response = service.calculate_roi(payload, user=None)
    
    # Перевірки
    mock_predict.assert_called_once_with("Computer Science", "United States")
    
    # Вартість навчання: 15000 * 4 = 60000
    assert response.total_education_investment == Decimal("60000.00")
    
    # Можливий місячний заробіток після завершення навчання.
    assert response.possible_monthly_salary == Decimal("4166.67")
    assert response.study_years == 4
    
    # Відсоток ROI має бути додатнім для таких вихідних даних
    assert response.roi_percent > 0
    assert len(response.career_growth_projection) == 11 # Рік 0 + 10 років


@patch("app.services.ai_rag_service.AIRAGService.predict_career_prospects")
def test_calculation_request_accepts_study_years(mock_predict, db_session):
    mock_predict.return_value = {"expected_start_salary": 50000.0}
    service = ROIService(db_session)
    payload = ROICalculationRequest(
        university="Test University",
        faculty="Computer Science",
        annual_tuition=Decimal("10000.00"),
    )

    response = service.calculate_roi(payload)

    # The service keeps calculation assumptions internal: four years by default,
    # with no user-supplied living cost, baseline income, tax, or probability.
    assert response.total_education_investment == Decimal("40000.00")

    custom_payload = ROICalculationRequest(
        university="Test University",
        faculty="Computer Science",
        annual_tuition=Decimal("10000.00"),
        study_years=3,
    )
    custom_response = service.calculate_roi(custom_payload)
    assert custom_response.study_years == 3
    assert custom_response.total_education_investment == Decimal("30000.00")

    with pytest.raises(ValidationError):
        ROICalculationRequest(
            university="Test University",
            faculty="Computer Science",
            annual_tuition=Decimal("10000.00"),
            expected_start_salary=Decimal("50000.00"),
        )


@patch("app.services.ai_rag_service.AIRAGService.predict_career_prospects")
def test_trial_endpoint_accepts_only_three_business_fields(mock_predict, client):
    mock_predict.return_value = {"expected_start_salary": 50000.0}

    response = client.post(
        "/api/roi/trial",
        json={
            "university": "Test University",
            "faculty": "Computer Science",
            "annual_tuition": "10000.00",
        },
    )

    assert response.status_code == 200
    assert response.json["total_education_investment"] == "40000.00"

    rejected = client.post(
        "/api/roi/trial",
        json={
            "university": "Test University",
            "faculty": "Computer Science",
            "annual_tuition": "10000.00",
            "tax_rate": "0.25",
        },
    )
    assert rejected.status_code == 422


@patch("app.services.ai_rag_service.AIRAGService.predict_career_prospects")
def test_career_analysis_returns_explainable_usd_json(mock_predict, client):
    mock_predict.return_value = {
        "expected_start_salary": 48000.0,
        "average_salary": 72000.0,
        "forecast_growth_percent": 4.0,
        "demand_score": 80,
        "ai_risk_score": 20,
    }
    response = client.post(
        "/api/roi/analyze",
        json={
            "university": "WSIiZ Rzeszów",
            "degree": "Informatyka — inżynier",
            "specialization_focus": "Web Development + Mobile Applications",
            "country": "Poland",
            "currency": "USD",
            "study_years": 3.5,
            "monthly_payment": 930,
            "payments_per_year": 10,
            "additional_learning_budget_min": 0,
            "additional_learning_budget_max": 5000,
        },
    )
    assert response.status_code == 200
    body = response.json
    assert body["education"]["total_tuition"]["min"] == "32550.00"
    assert body["education"]["study_years"] == "3.5"
    assert body["salary_forecast_in_today_money"]["currency"] == "USD"
    assert body["roi"]["payback_months"]["min"] > 0


@patch("app.services.ai_rag_service.AIRAGService.predict_career_prospects")
def test_trial_returns_and_persists_full_career_analysis(mock_predict, client, db_session):
    mock_predict.return_value = {
        "expected_start_salary": 48000.0,
        "average_salary": 72000.0,
        "forecast_growth_percent": 4.0,
        "demand_score": 80,
        "ai_risk_score": 20,
    }
    response = client.post(
        "/api/roi/trial",
        json={
            "university": "Demo University",
            "degree": "Computer Science — Bachelor",
            "specialization_focus": "Web Development + Mobile Applications",
            "country": "Poland",
            "currency": "USD",
            "study_years": 3.5,
            "monthly_payment": 930,
            "payments_per_year": 10,
            "additional_learning_budget_min": 0,
            "additional_learning_budget_max": 100,
        },
    )

    assert response.status_code == 200
    assert response.json["education"]["total_investment"]["min"] == "32550.00"
    from app.models import CareerAnalysis, CareerEducation, CareerSalaryBand
    analysis = db_session.query(CareerAnalysis).one()
    assert analysis.user_id is None
    assert analysis.education.tuition_min == Decimal("32550.00")
    assert analysis.education.learning_budget_max == Decimal("100.00")
    assert len(analysis.salary_forecast.bands) == 4
    assert db_session.query(CareerEducation).count() == 1
    assert db_session.query(CareerSalaryBand).count() == 4
