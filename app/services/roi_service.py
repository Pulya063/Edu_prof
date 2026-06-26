from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ROICalculation, User
from app.schemas import ROICalculationRequest, ROICalculationResponse

MONEY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.01")


class ROIService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    def calculate_roi(self, payload: ROICalculationRequest, user: User | None = None) -> ROICalculationResponse:
        total_cost = payload.tuition_cost * Decimal(payload.study_duration_years)
        projected_income_5y = self.calculate_income_projection(
            payload.expected_salary_after_graduation,
            payload.annual_salary_growth_percent,
            years=5,
        )
        projected_income_10y = self.calculate_income_projection(
            payload.expected_salary_after_graduation,
            payload.annual_salary_growth_percent,
            years=10,
        )
        roi_percent = ((projected_income_10y - total_cost) / total_cost * Decimal("100")).quantize(
            PERCENT_QUANT,
            rounding=ROUND_HALF_UP,
        )
        break_even_months = self.calculate_break_even(
            total_cost=total_cost,
            starting_salary=payload.expected_salary_after_graduation,
            annual_growth_percent=payload.annual_salary_growth_percent,
        )
        career_growth_projection = [
            self.calculate_income_projection(
                payload.expected_salary_after_graduation,
                payload.annual_salary_growth_percent,
                years=year,
            )
            for year in range(1, 11)
        ]

        response = ROICalculationResponse(
            roi_percent=roi_percent,
            break_even_months=break_even_months,
            projected_income_5y=projected_income_5y,
            projected_income_10y=projected_income_10y,
            total_education_investment=total_cost.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP),
            career_growth_projection=career_growth_projection,
        )

        if user is not None:
            calculation = ROICalculation(
                user_id=user.id,
                program_id=payload.program_id,
                total_cost=response.total_education_investment,
                roi_percent=response.roi_percent,
                break_even_months=response.break_even_months,
                projected_income_5y=response.projected_income_5y,
                projected_income_10y=response.projected_income_10y,
            )
            self.db.add(calculation)
            self.db.commit()

        return response

    def calculate_break_even(
        self,
        total_cost: Decimal,
        starting_salary: Decimal,
        annual_growth_percent: Decimal,
    ) -> int:
        monthly_income = starting_salary / Decimal("12")
        monthly_growth = (annual_growth_percent / Decimal("100")) / Decimal("12")
        accumulated = Decimal("0")
        months = 0

        while accumulated < total_cost and months < 1200:
            accumulated += monthly_income
            monthly_income *= Decimal("1") + monthly_growth
            months += 1

        return months

    def calculate_income_projection(
        self,
        starting_salary: Decimal,
        annual_growth_percent: Decimal,
        years: int,
    ) -> Decimal:
        total = Decimal("0")
        growth_multiplier = Decimal("1") + (annual_growth_percent / Decimal("100"))
        current_salary = starting_salary
        for _ in range(years):
            total += current_salary
            current_salary *= growth_multiplier
        return total.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

    def get_history(self, user: User) -> list[ROICalculationResponse]:
        result = self.db.execute(
            select(ROICalculation)
            .where(ROICalculation.user_id == user.id)
            .order_by(desc(ROICalculation.created_at))
        )
        calculations = result.scalars().all()
        return [
            ROICalculationResponse(
                roi_percent=item.roi_percent,
                break_even_months=item.break_even_months,
                projected_income_5y=item.projected_income_5y,
                projected_income_10y=item.projected_income_10y,
                total_education_investment=item.total_cost,
                career_growth_projection=[],
            )
            for item in calculations
        ]
