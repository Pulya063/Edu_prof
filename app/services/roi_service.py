"""
roi_service.py — розрахунок ROI освіти.

Формули базуються на моделі людського капіталу (Mincer, 1974) та
    детермінованих фінансових показниках та моделі Мінсера.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ROICalculation, User
from app.schemas import CareerAnalysisRequest, ROICalculationRequest, ROICalculationResponse
from app.core.logging_config import log_call

logger = logging.getLogger(__name__)

MONEY   = Decimal("0.01")
PERCENT = Decimal("0.01")
METHODOLOGY_VERSION = "v2-scenario"
DEFAULT_COUNTRY = "United States"

# ── Ставки зростання зарплати по роках досвіду (модель Мінсера) ──────────────
# Джерело: Mincer J. (1974), ОЕСР Education at a Glance 2023
# Рік 1–3: швидке зростання (+8%) — навчання на роботі
# Рік 4–6: стабільне зростання (+5%) — спеціаліст
# Рік 7–10: уповільнення (+3%) — старший фахівець
# Рік 11+: плато (+2%) — приріст дорівнює інфляції
from app.services.ai_rag_service import MINCER_GROWTH_RATES, MINCER_PLATEAU


def _mincer_rate(year: int) -> Decimal:
    """Повертає ставку зростання зарплати для року досвіду за моделлю Мінсера."""
    for rng, rate in MINCER_GROWTH_RATES.items():
        if year in rng:
            return rate
    return MINCER_PLATEAU


def _money(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _range(low: Decimal, high: Decimal) -> dict[str, int]:
    return {"min": _money(low), "max": _money(high)}


class ROIService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session

    # ── Основний розрахунок ─────────────────────────────────────────────────

    @log_call
    def calculate_roi(
        self,
        payload: ROICalculationRequest,
        user: User | None = None,
    ) -> ROICalculationResponse:
        logger.info("Starting ROI calculation user_id=%s", getattr(user, "id", "anonymous"))
        
        from app.services.ai_rag_service import AIRAGService

        ai_service = AIRAGService()
        prospects = ai_service.predict_career_prospects(payload.faculty, DEFAULT_COUNTRY)
        start_salary = Decimal(str(prospects.get("expected_start_salary", 45000.0)))

        tuition = payload.annual_tuition
            
        study_years = payload.study_years
        total_cost = (tuition * Decimal(study_years)).quantize(
            MONEY, rounding=ROUND_HALF_UP
        )

        # Деталізований прогноз по роках (рік 0 = стартова зарплата)
        yearly_projection = self._yearly_salaries(start_salary, years=10)

        # Сумарний дохід за 10 років для розрахунку ROI
        cumulative_10y = sum(yearly_projection[1:11], Decimal("0"))

        # ROI = (сумарний дохід за 10р − витрати) / витрати × 100
        roi_percent = ((cumulative_10y - total_cost) / total_cost * Decimal("100")).quantize(
            PERCENT, rounding=ROUND_HALF_UP
        )

        break_even_months = self._break_even(
            total_cost,
            start_salary,
        )

        possible_monthly_salary = (start_salary / Decimal("12")).quantize(MONEY, rounding=ROUND_HALF_UP)

        response = ROICalculationResponse(
            roi_percent=roi_percent,
            break_even_months=break_even_months,
            total_education_investment=total_cost,
            career_growth_projection=yearly_projection,
            study_years=study_years,
            possible_monthly_salary=possible_monthly_salary,
            methodology_version=METHODOLOGY_VERSION,
        )

        if user is not None:
            self._save(user, payload, response, prospects)

        return response

    @log_call
    def analyze_career(self, payload: CareerAnalysisRequest) -> dict:
        """Build a concise decision JSON; money is always USD and math is deterministic."""
        from app.services.ai_rag_service import AIRAGService

        prospects = AIRAGService().predict_career_prospects(payload.specialization_focus, payload.country)
        start_salary = Decimal(str(prospects.get("expected_start_salary", 45000))).quantize(MONEY)
        average_salary = Decimal(str(prospects.get("average_salary", start_salary * Decimal("1.33")))).quantize(MONEY)
        growth = Decimal(str(prospects.get("forecast_growth_percent", 3))).quantize(PERCENT)
        demand = max(0, min(100, int(prospects.get("demand_score", 70))))
        ai_risk = max(0, min(100, int(prospects.get("ai_risk_score", 30))))

        base_tuition = (payload.monthly_payment * payload.payments_per_year * payload.study_years).quantize(MONEY)
        fee_adjusted_tuition = (base_tuition * Decimal("1.12")).quantize(MONEY)
        total_low = base_tuition + payload.additional_learning_budget_min
        total_high = fee_adjusted_tuition + payload.additional_learning_budget_max

        salary = {
            "currency": "USD",
            "intern_or_trainee": {"monthly_min": _money(start_salary * Decimal("0.55")), "monthly_max": _money(start_salary * Decimal("0.85"))},
            "junior_0_2_years": {"monthly_min": _money(start_salary * Decimal("0.85")), "monthly_max": _money(start_salary * Decimal("1.15")), "realistic_target": _range(start_salary * Decimal("0.95"), start_salary * Decimal("1.05"))},
            "mid_2_5_years": {"monthly_min": _money(average_salary * Decimal("0.90")), "monthly_max": _money(average_salary * Decimal("1.35"))},
            "senior_5_plus_years": {"monthly_min": _money(average_salary * Decimal("1.30")), "monthly_max": _money(average_salary * Decimal("2.00"))},
            "note": "Оцінка в сьогоднішніх USD; це не гарантія зарплати.",
        }
        realistic_monthly = start_salary / Decimal("12")
        payback_low = max(1, int((total_low / realistic_monthly).to_integral_value(rounding=ROUND_HALF_UP)))
        payback_high = max(payback_low, int((total_high / realistic_monthly).to_integral_value(rounding=ROUND_HALF_UP)))
        first_year_low = (((realistic_monthly * Decimal("0.95") * 12 - total_high) / total_high) * 100).quantize(PERCENT)
        first_year_high = (((realistic_monthly * Decimal("1.05") * 12 - total_low) / total_low) * 100).quantize(PERCENT)
        probability = max(45, min(90, round(55 + demand * 0.3 - ai_risk * 0.15)))
        focus = payload.specialization_focus.lower()
        skills = ["Git + GitHub", "SQL + PostgreSQL", "REST API", "testing", "Docker", "English B2+"]
        if "web" in focus or "mobile" in focus:
            skills[0:0] = ["JavaScript + TypeScript", "React / Next.js", "Mobile development basics"]
        skills.extend(["cloud basics", "AI API / LLM integration"])

        result = {
            "education": {"university": payload.university, "degree": payload.degree, "specialization": payload.specialization_focus, "country": payload.country, "study_years": payload.study_years, "currency": "USD", "total_tuition": {"min": base_tuition, "max": fee_adjusted_tuition}, "additional_learning_budget": {"min": payload.additional_learning_budget_min, "max": payload.additional_learning_budget_max}, "total_investment": {"min": total_low, "max": total_high}, "living_costs_included": payload.include_living_costs},
            "salary_forecast_in_today_money": salary,
            "roi": {"payback_likely": probability >= 65, "estimated_probability_percent": probability, "payback_months": {"min": payback_low, "max": payback_high}, "first_year_roi_percent": {"min": first_year_low, "max": first_year_high}, "long_term_roi": "high" if probability >= 70 else "moderate", "condition": "Практичний досвід і portfolio до завершення навчання суттєво підвищують шанс окупності."},
            "extra_courses": {"required": False, "recommended": True, "paid_courses_required": False, "recommendation": "Платні курси не обов'язкові; portfolio, практика й code review важливіші."},
            "skills_to_learn_outside_university": skills,
            "recommended_strategy": {"year_1": "Основи програмування, Git, SQL і 2–3 невеликі проєкти.", "year_2": "Frontend/backend stack, PostgreSQL, Docker і перша практика.", "year_3": "Junior/Intern робота, production-проєкти та підготовка portfolio.", "final_stage": "Диплом має доповнювати практичний досвід, а не замінювати його."},
            "biggest_risk": {"risk": "Завершити навчання без комерційного або проєктного досвіду.", "result": "Диплом сам по собі не гарантує позицію Junior Developer."},
            "market_outlook": {"web_only": "moderate", "web_plus_backend": "good", "mobile": "good", "fullstack": "good", "web_plus_ai": "very_good", "backend_plus_ai": "very_good"},
            "scores": {"university_value": None, "degree_value": None, "career_potential": round((demand + (100 - ai_risk)) / 20, 1), "data_confidence": probability},
            "assumptions": ["Всі суми у USD.", "Зарплата вказана gross до податків.", "Витрати на проживання не включені.", "Комісії, інфляція та зміна курсу не прогнозуються."],
            "verdict": "Ймовірно варто, якщо паралельно з навчанням створювати portfolio та отримати практичний досвід до випуску.",
        }
        self._save_career_analysis(payload, result)
        return result

    def _save_career_analysis(self, payload: CareerAnalysisRequest, result: dict, user_id: int | None = None) -> None:
        """Persist the important analysis facts in normalized tables.

        Trial requests are intentionally anonymous, therefore ``user_id`` is
        nullable. The response remains the API representation; the database
        stores facts in related tables rather than a JSON blob.
        """
        from app.models import (
            CareerAnalysis, CareerEducation, CareerInsight, CareerROI,
            CareerSalaryBand, CareerSalaryForecast, CareerScores,
        )

        education = result["education"]
        salary = result["salary_forecast_in_today_money"]
        roi = result["roi"]
        scores = result["scores"]
        analysis = CareerAnalysis(
            user_id=user_id,
            university=payload.university,
            degree=payload.degree,
            specialization=payload.specialization_focus,
            country=payload.country,
            currency=payload.currency,
            study_years=payload.study_years,
            living_costs_included=payload.include_living_costs,
            education=CareerEducation(
                tuition_min=education["total_tuition"]["min"],
                tuition_max=education["total_tuition"]["max"],
                learning_budget_min=education["additional_learning_budget"]["min"],
                learning_budget_max=education["additional_learning_budget"]["max"],
                investment_min=education["total_investment"]["min"],
                investment_max=education["total_investment"]["max"],
            ),
            salary_forecast=CareerSalaryForecast(
                currency=salary["currency"],
                bands=[
                    CareerSalaryBand(
                        stage=stage,
                        monthly_min=band["monthly_min"],
                        monthly_max=band["monthly_max"],
                        realistic_target_min=band.get("realistic_target", {}).get("min"),
                        realistic_target_max=band.get("realistic_target", {}).get("max"),
                    )
                    for stage, band in salary.items()
                    if stage != "currency" and stage != "note"
                ],
            ),
            roi=CareerROI(
                payback_likely=roi["payback_likely"],
                probability_percent=roi["estimated_probability_percent"],
                payback_months_min=roi["payback_months"]["min"],
                payback_months_max=roi["payback_months"]["max"],
                first_year_roi_min=roi["first_year_roi_percent"]["min"],
                first_year_roi_max=roi["first_year_roi_percent"]["max"],
                long_term_roi=roi["long_term_roi"],
            ),
            scores=CareerScores(
                career_potential=scores["career_potential"],
                data_confidence=scores["data_confidence"],
            ),
        )
        for kind, name, content in (
            ("strategy", key, value) for key, value in result["recommended_strategy"].items()
        ):
            analysis.insights.append(CareerInsight(kind=kind, name=name, content=content))
        analysis.insights.extend([
            CareerInsight(kind="risk", name="biggest_risk", content=result["biggest_risk"]["risk"]),
            CareerInsight(kind="risk", name="risk_result", content=result["biggest_risk"]["result"]),
            CareerInsight(kind="recommendation", name="verdict", content=result["verdict"]),
            *[
                CareerInsight(kind="skill", name="skill", content=skill)
                for skill in result["skills_to_learn_outside_university"]
            ],
        ])
        self.db.add(analysis)
        self.db.commit()

    # ── Допоміжні методи ────────────────────────────────────────────────────

    @log_call
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

    @log_call
    def _break_even(
        self,
        total_cost: Decimal,
        starting_salary: Decimal,
    ) -> int:
        """
        Кількість місяців після закінчення навчання до повної окупності витрат.
        Зарплата зростає щомісяця за ставкою Мінсера (річна / 12).
        """
        monthly = starting_salary / Decimal("12")
        if monthly <= 0:
            return 1200
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

    @log_call
    def _save(self, user: User, payload: ROICalculationRequest, resp: ROICalculationResponse, prospects: dict | None = None) -> None:
        from app.models import ROICalculation, SalaryStatistic, CareerForecast
        import datetime
        
        calc = ROICalculation(
            user_id=user.id,
            # The three-field request has no program identifier; keep the
            # legacy relation nullable until program selection is reintroduced.
            program_id=None,
            total_cost=resp.total_education_investment,
            roi_percent=resp.roi_percent,
            break_even_months=resp.break_even_months,
            study_years=resp.study_years,
            possible_monthly_salary=resp.possible_monthly_salary,
            methodology_version=resp.methodology_version,
        )
        self.db.add(calc)
        
        if prospects is not None:
            stat = SalaryStatistic(
                profession=payload.faculty,
                country=DEFAULT_COUNTRY,
                average_salary=Decimal(str(prospects.get("average_salary", 60000.0))),
                growth_rate=Decimal(str(prospects.get("forecast_growth_percent", 3.0)))
            )
            self.db.add(stat)
            
            forecast = CareerForecast(
                profession=payload.faculty,
                demand_score=int(prospects.get("demand_score", 70)),
                ai_risk_score=int(prospects.get("ai_risk_score", 30)),
                forecast_growth_percent=Decimal(str(prospects.get("forecast_growth_percent", 3.0))),
                forecast_year=datetime.datetime.now().year + 5
            )
            self.db.add(forecast)
            
        self.db.commit()

    # ── Історія ─────────────────────────────────────────────────────────────

    @log_call
    def get_history(self, user: User) -> list[ROICalculationResponse]:
        logger.info("Loading ROI history user_id=%s", user.id)
        rows = self.db.execute(
            select(ROICalculation)
            .where(ROICalculation.user_id == user.id, ROICalculation.deleted_at.is_(None))
            .order_by(desc(ROICalculation.created_at))
        ).scalars().all()

        return self.serialize_history(rows)

    def serialize_history(self, rows: list[ROICalculation]) -> list[ROICalculationResponse]:
        return [
            ROICalculationResponse(
                id=r.id,
                roi_percent=r.roi_percent,
                break_even_months=r.break_even_months,
                total_education_investment=r.total_cost,
                career_growth_projection=[],
                study_years=r.study_years,
                possible_monthly_salary=r.possible_monthly_salary,
                methodology_version=r.methodology_version,
                created_at=r.created_at,
            )
            for r in rows
        ]
