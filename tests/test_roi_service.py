import pytest
from decimal import Decimal
from unittest.mock import patch

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
        degree_program="Computer Science",
        country="United States",
        tuition_cost=Decimal("15000.00"),
        study_duration_years=4,
        expected_start_salary=None # Залишаємо None, щоб викликався mock_predict
    )
    
    response = service.calculate_roi(payload, user=None)
    
    # Перевірки
    mock_predict.assert_called_once_with("Computer Science", "United States")
    
    # Вартість навчання: 15000 * 4 = 60000
    assert response.total_education_investment == Decimal("60000.00")
    
    # Прогнозований дохід через 5 років (має бути більший за базові 50к / 12)
    assert response.projected_income_5y > Decimal("4000.00")
    
    # Відсоток ROI має бути додатнім для таких вихідних даних
    assert response.roi_percent > 0
    assert len(response.career_growth_projection) == 11 # Рік 0 + 10 років
