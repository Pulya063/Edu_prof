"""
roi_service.py — розрахунок ROI освіти.

Формули базуються на моделі людського капіталу (Mincer, 1974) та
стандартних фінансових показниках NPV/IRR.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ROICalculation, User
from app.schemas import ROICalculationRequest, ROICalculationResponse

MONEY   = Decimal("0.01")
PERCENT = Decimal("0.01")

# ── Ставки зростання зарплати по роках досвіду (модель Мінсера) ──────────────
# Джерело: Mincer J. (1974), ОЕСР Education at a Glance 2023
# Рік 1–3: швидке зростання (+8%) — навчання на роботі
# Рік 4–6: стабільне зростання (+5%) — спеціаліст
# Рік 7–10: уповільнення (+3%) — старший фахівець
# Рік 11+: плато (+2%) — приріст дорівнює інфляції
MINCER_GROWTH_RATES = {
    range(1, 4):   Decimal("0.08"),
    range(4, 7):   Decimal("0.05"),
    range(7, 11):  Decimal("0.03"),
}
MINCER_PLATEAU = Decimal("0.02")


def _mincer_rate(year: int) -> Decimal:
    """Повертає ставку зростання зарплати для року досвіду за моделлю Мінсера."""
    for rng, rate in MINCER_GROWTH_RATES.items():
        if year in rng:
            return rate
    return MINCER_PLATEAU


class ROIService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    # ── Основний розрахунок ─────────────────────────────────────────────────

    def calculate_roi(
        self,
        payload: ROICalculationRequest,
        user: User | None = None,
    ) -> ROICalculationResponse:

        total_cost = (payload.tuition_cost * Decimal(payload.study_duration_years)).quantize(
            MONEY, rounding=ROUND_HALF_UP
        )

        # Прогнози доходу
        projected_5y  = self._cumulative_income(payload.expected_salary_after_graduation, years=5)
        projected_10y = self._cumulative_income(payload.expected_salary_after_graduation, years=10)

        # ROI = (сумарний дохід за 10р − витрати) / витрати × 100
        roi_percent = ((projected_10y - total_cost) / total_cost * Decimal("100")).quantize(
            PERCENT, rounding=ROUND_HALF_UP
        )

        break_even_months = self._break_even(total_cost, payload.expected_salary_after_graduation)

        # Деталізований прогноз по роках (рік 0 = стартова зарплата)
        yearly_projection = self._yearly_salaries(payload.expected_salary_after_graduation, years=10)

        response = ROICalculationResponse(
            roi_percent=roi_percent,
            break_even_months=break_even_months,
            projected_income_5y=projected_5y,
            projected_income_10y=projected_10y,
            total_education_investment=total_cost,
            career_growth_projection=yearly_projection,
        )

        if user is not None:
            self._save(user, payload, response)

        return response

    # ── Допоміжні методи ────────────────────────────────────────────────────

    def _yearly_salaries(self, start: Decimal, years: int) -> list[Decimal]:
        """
        Повертає список річних зарплат по моделі Мінсера.
        yearly_salaries[0] = стартова зарплата (рік 0 = одразу після навчання).
        """
        salaries = [start.quantize(MONEY, rounding=ROUND_HALF_UP)]
        current = start
        for yr in range(1, years + 1):
            current = (current * (Decimal("1") + _mincer_rate(yr))).quantize(
                MONEY, rounding=ROUND_HALF_UP
            )
            salaries.append(current)
        return salaries

    def _cumulative_income(self, start: Decimal, years: int) -> Decimal:
        """Сума доходів за N років (модель Мінсера)."""
        salaries = self._yearly_salaries(start, years)
        # salaries[0] — рік 0 (стартовий), salaries[1..N] — роки 1..N
        return sum(salaries[1:], Decimal("0")).quantize(MONEY, rounding=ROUND_HALF_UP)

    def _break_even(self, total_cost: Decimal, starting_salary: Decimal) -> int:
        """
        Кількість місяців після закінчення навчання до повної окупності витрат.
        Зарплата зростає щомісяця за ставкою Мінсера (річна / 12).
        """
        monthly = starting_salary / Decimal("12")
        accumulated = Decimal("0")
        months = 0
        year = 1  # рік досвіду

        while accumulated < total_cost and months < 1200:
            months += 1
            accumulated += monthly
            # Щомісячне зростання = річна ставка / 12
            monthly_rate = _mincer_rate(year) / Decimal("12")
            monthly *= Decimal("1") + monthly_rate
            if months % 12 == 0:
                year += 1

        return months

    def _save(self, user: User, payload: ROICalculationRequest, resp: ROICalculationResponse) -> None:
        calc = ROICalculation(
            user_id=user.id,
            program_id=payload.program_id,
            total_cost=resp.total_education_investment,
            roi_percent=resp.roi_percent,
            break_even_months=resp.break_even_months,
            projected_income_5y=resp.projected_income_5y,
            projected_income_10y=resp.projected_income_10y,
        )
        self.db.add(calc)
        self.db.commit()

    # ── Історія ─────────────────────────────────────────────────────────────

    def get_history(self, user: User) -> list[ROICalculationResponse]:
        rows = self.db.execute(
            select(ROICalculation)
            .where(ROICalculation.user_id == user.id)
            .order_by(desc(ROICalculation.created_at))
        ).scalars().all()

        return [
            ROICalculationResponse(
                roi_percent=r.roi_percent,
                break_even_months=r.break_even_months,
                projected_income_5y=r.projected_income_5y,
                projected_income_10y=r.projected_income_10y,
                total_education_investment=r.total_cost,
                career_growth_projection=[],
            )
            for r in rows
        ]
