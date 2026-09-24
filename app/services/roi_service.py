from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
import logging
import numpy as np
import pandas as pd

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ROICalculation, User
from app.schemas import CareerAnalysisRequest, ROICalculationResponse, TrialROIRequest
from app.core.logging_config import log_call
from app.services.market_data_service import MarketDataService
from app.services.onet_service import OnetService
from app.services.ai_rag_service import AIRAGService


logger = logging.getLogger(__name__)

MONEY   = Decimal("0.01")
PERCENT = Decimal("0.01")
METHODOLOGY_VERSION = "v3-numpy"
DEFAULT_COUNTRY = "United States"

# ── Ставки зростання зарплати по роках досвіду (модель Мінсера) ──────────────
MINCER_GROWTH_RATES = {
    range(1, 4):   Decimal("0.08"),
    range(4, 7):   Decimal("0.05"),
    range(7, 11):  Decimal("0.03"),
}
MINCER_PLATEAU = Decimal("0.02")


def _mincer_rate(year: int) -> Decimal:
    for rng, rate in MINCER_GROWTH_RATES.items():
        if year in rng:
            return rate
    return MINCER_PLATEAU

def _money(value: float) -> int:
    return int(round(value))

def _range(low: float, high: float) -> dict[str, int]:
    return {"min": _money(low), "max": _money(high)}

class ROIService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.market_service = MarketDataService()
        self.ai_service = AIRAGService()
        self.onet_service = OnetService()

    @log_call
    def analyze_trial(self, payload: TrialROIRequest) -> dict:
        """Lightweight analysis for trial without full projections and DB saving."""
        prospects = self.market_service.predict_career_prospects(payload.faculty, DEFAULT_COUNTRY)
        start_salary = float(prospects.get("expected_start_salary", 45000))

        total_investment = float(payload.annual_tuition * payload.study_years)

        realistic_monthly = start_salary / 12.0
        payback_months = max(1, int(round(total_investment / realistic_monthly))) if realistic_monthly > 0 else 1200
        first_year_roi = (((realistic_monthly * 0.95 * 12 - total_investment) / total_investment) * 100) if total_investment > 0 else 0

        return {
            "education": {
                "specialization": payload.faculty,
                "total_investment": {"min": round(total_investment, 2)},
            },
            "roi": {
                "payback_months": {"min": payback_months},
                "first_year_roi_percent": {"min": round(first_year_roi, 2)},
            },
        }

    @log_call
    def analyze_career(self, payload: CareerAnalysisRequest, user_id: int | None = None) -> dict:
        prospects = self.market_service.predict_career_prospects(payload.specialization_focus, payload.country)
        
        start_salary = float(prospects.get("expected_start_salary", 45000))
        average_salary = float(prospects.get("average_salary", start_salary * 1.33))
        # Fetch fresh market context from O*NET if configured
        onet_data = self.onet_service.get_profession_data(payload.specialization_focus)
        
        # Override CSV data with real O*NET data if found
        if onet_data.get("found"):
            demand = onet_data["demand_score"]
            ai_risk = onet_data["ai_risk_score"]
        else:
            demand = max(0, min(100, int(prospects.get("demand_score", 70))))
            ai_risk = max(0, min(100, int(prospects.get("ai_risk_score", 30))))


        base_tuition = float(payload.monthly_payment * payload.payments_per_year * payload.study_years)
        fee_adjusted_tuition = base_tuition * 1.12
        
        # Витрати на освіту
        budget_min = float(payload.additional_learning_budget_min)
        budget_max = float(payload.additional_learning_budget_max)
        investment_arr = np.array([
            base_tuition + budget_min,
            fee_adjusted_tuition + budget_max
        ])
        total_low, total_high = float(investment_arr[0]), float(investment_arr[1])

        realistic_monthly = start_salary / 12.0
        
        # Окупність (в місяцях) через numpy
        payback_arr = np.where(
            realistic_monthly > 0, 
            np.maximum(1, np.round(investment_arr / realistic_monthly)), 
            1200
        ).astype(int)
        payback_low, payback_high = int(payback_arr[0]), int(payback_arr[1])
        
        # ROI першого року через numpy
        first_year_incomes = np.array([realistic_monthly * 0.95 * 12, realistic_monthly * 1.05 * 12])
        # investment_arr: [low, high]. Для max_roi беремо max income і min investment
        first_year_roi_arr = np.where(
            investment_arr > 0,
            ((first_year_incomes[::-1] - investment_arr) / investment_arr) * 100,
            0
        )
        first_year_high, first_year_low = float(first_year_roi_arr[0]), float(first_year_roi_arr[1])

        # Зарплатні грейди через Pandas
        df_salary = pd.DataFrame([
            {"stage": "intern_or_trainee", "monthly_min": start_salary * 0.55, "monthly_max": start_salary * 0.85},
            {"stage": "junior_0_2_years", "monthly_min": start_salary * 0.85, "monthly_max": start_salary * 1.15, "realistic_target_min": start_salary * 0.95, "realistic_target_max": start_salary * 1.05},
            {"stage": "mid_2_5_years", "monthly_min": average_salary * 0.90, "monthly_max": average_salary * 1.35},
            {"stage": "senior_5_plus_years", "monthly_min": average_salary * 1.30, "monthly_max": average_salary * 2.00}
        ])
        
        for col in ["monthly_min", "monthly_max", "realistic_target_min", "realistic_target_max"]:
            df_salary[col] = df_salary[col].apply(lambda x: _money(x) if pd.notna(x) else None)
            
        salary = {
            "currency": "USD",
            "note": "Оцінка в сьогоднішніх USD; це не гарантія зарплати."
        }
        for _, row in df_salary.iterrows():
            stage = row["stage"]
            band = {"monthly_min": int(row["monthly_min"]), "monthly_max": int(row["monthly_max"])}
            if pd.notna(row.get("realistic_target_min")):
                band["realistic_target"] = {"min": int(row["realistic_target_min"]), "max": int(row["realistic_target_max"])}
            salary[stage] = band
        
        probability = max(45, min(90, round(55 + demand * 0.3 - ai_risk * 0.15)))
        
        # Prepare statistical data for AI
        stats_for_ai = {
            "profession": payload.specialization_focus,
            "country": payload.country,
            "start_salary": start_salary,
            "average_salary": average_salary,
            "investment_min": round(total_low, 2),
            "investment_max": round(total_high, 2),
            "payback_low": payback_low,
            "payback_high": payback_high,
            "first_year_low": round(first_year_low, 2),
            "first_year_high": round(first_year_high, 2),
            "ai_risk": ai_risk,
            "demand": demand,
            "real_skills_from_onet": onet_data.get("skills", [])
        }
        
        # Call AI to get qualitative insights
        ai_insights = self.ai_service.generate_qualitative_insights(stats_for_ai)
        
        skills = ai_insights.get("skills_to_learn_outside_university", [])
        recommended_strategy = ai_insights.get("recommended_strategy", {})
        biggest_risk = ai_insights.get("biggest_risk", {})
        verdict = ai_insights.get("verdict", "")

        result = {
            "education": {"university": payload.university, "degree": payload.degree, "specialization": payload.specialization_focus, "country": payload.country, "study_years": payload.study_years, "currency": "USD", "total_tuition": {"min": round(base_tuition,2), "max": round(fee_adjusted_tuition,2)}, "additional_learning_budget": {"min": payload.additional_learning_budget_min, "max": payload.additional_learning_budget_max}, "total_investment": {"min": round(total_low,2), "max": round(total_high,2)}, "living_costs_included": payload.include_living_costs},
            "salary_forecast_in_today_money": salary,
            "roi": {"payback_likely": probability >= 65, "estimated_probability_percent": probability, "payback_months": {"min": payback_low, "max": payback_high}, "first_year_roi_percent": {"min": round(first_year_low,2), "max": round(first_year_high,2)}, "long_term_roi": "high" if probability >= 70 else "moderate", "condition": "Практичний досвід і portfolio до завершення навчання суттєво підвищують шанс окупності."},
            "extra_courses": {"required": False, "recommended": True, "paid_courses_required": False, "recommendation": "Платні курси не обов'язкові; portfolio, практика й code review важливіші."},
            "skills_to_learn_outside_university": skills,
            "recommended_strategy": recommended_strategy,
            "biggest_risk": biggest_risk,
            "market_outlook": {"web_only": "moderate", "web_plus_backend": "good", "mobile": "good", "fullstack": "good", "web_plus_ai": "very_good", "backend_plus_ai": "very_good"},
            "scores": {"university_value": None, "degree_value": None, "career_potential": round((demand + (100 - ai_risk)) / 20, 1), "data_confidence": probability},
            "assumptions": ["Всі ціни в USD.", "Доходи є gross до податків.", "Увага на ризики ШІ та конкуренцію."],
            "verdict": verdict,
        }
        
        # Перетворення результату у Pandas Series та назад у словник (як демонстрація Data-Driven підходу)
        df_result = pd.Series(result).to_dict()
        
        self._save_career_analysis(payload, df_result, user_id=user_id)
        return df_result

    def _save_career_analysis(self, payload: CareerAnalysisRequest, result: dict, user_id: int | None = None) -> None:
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

    @log_call
    def get_history(self, user: User) -> list[ROICalculationResponse]:
        logger.info("Loading ROI history user_id=%s", user.id)
        rows = self.db.execute(
            select(ROICalculation)
            .where(ROICalculation.user_id == user.id, ROICalculation.deleted_at.is_(None))
            .order_by(desc(ROICalculation.created_at))
        ).scalars().all()

        return self.serialize_history(rows)



    @log_call
    def get_full_history(self, user: User) -> list[dict]:
        """Return a merged, chronologically sorted list of all analyses for the user.

        Combines records from the new ``CareerAnalysis`` table (used by ``/api/roi/analyze``)
        and the legacy ``ROICalculation`` table (used by the old ``/api/roi/calculate``)
        into a single unified response shape.
        """
        from sqlalchemy.orm import joinedload
        from app.models import CareerAnalysis

        # ── New career analyses (from /api/roi/analyze) ─────────────────────
        analyses = self.db.execute(
            select(CareerAnalysis)
            .options(
                joinedload(CareerAnalysis.education),
                joinedload(CareerAnalysis.roi),
            )
            .where(CareerAnalysis.user_id == user.id)
            .order_by(desc(CareerAnalysis.created_at))
        ).unique().scalars().all()

        items: list[dict] = []
        for a in analyses:
            roi = a.roi
            edu = a.education
            items.append({
                "id": a.id,
                "source": "career_analysis",
                "university": a.university,
                "specialization": a.specialization,
                "degree": a.degree,
                "country": a.country,
                "study_years": float(a.study_years),
                "total_investment_min": float(edu.investment_min) if edu else None,
                "total_investment_max": float(edu.investment_max) if edu else None,
                "roi_first_year_min": float(roi.first_year_roi_min) if roi else None,
                "roi_first_year_max": float(roi.first_year_roi_max) if roi else None,
                "payback_months_min": roi.payback_months_min if roi else None,
                "payback_months_max": roi.payback_months_max if roi else None,
                "payback_likely": roi.payback_likely if roi else None,
                "long_term_roi": roi.long_term_roi if roi else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

        # ── Legacy ROI calculations (from /api/roi/calculate) ────────────────
        legacy_rows = self.db.execute(
            select(ROICalculation)
            .where(ROICalculation.user_id == user.id, ROICalculation.deleted_at.is_(None))
            .order_by(desc(ROICalculation.created_at))
        ).scalars().all()

        for r in legacy_rows:
            items.append({
                "id": r.id,
                "source": "roi_calculation",
                "university": None,
                "specialization": None,
                "degree": None,
                "country": None,
                "study_years": float(r.study_years),
                "total_investment_min": float(r.total_cost),
                "total_investment_max": float(r.total_cost),
                "roi_first_year_min": float(r.roi_percent),
                "roi_first_year_max": float(r.roi_percent),
                "payback_months_min": r.break_even_months,
                "payback_months_max": r.break_even_months,
                "payback_likely": None,
                "long_term_roi": None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

        # Sort merged list by date, newest first
        items.sort(key=lambda x: x["created_at"] or "", reverse=True)
        return items

