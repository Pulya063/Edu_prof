from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import db

class BaseIDMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ReprMixin:
    repr_fields: ClassVar[tuple[str, ...]] = ("id",)

    def __repr__(self) -> str:
        values = ", ".join(f"{field}={getattr(self, field)!r}" for field in self.repr_fields)
        return f"{self.__class__.__name__}({values})"


class User(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "users"
    repr_fields = ("id", "email")

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    plan: Mapped[str] = mapped_column(String(20), default="Free", server_default="Free", nullable=False)
    workspace_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")

    roi_calculations: Mapped[list["ROICalculation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    roadmaps: Mapped[list["UserRoadmap"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    motivation_letters: Mapped[list["MotivationLetter"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    simulation_scenarios: Mapped[list["SimulationScenario"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class University(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "universities"
    __table_args__ = (Index("ix_universities_country_name", "country", "name"),)
    repr_fields = ("id", "name")

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    programs: Mapped[list["EducationProgram"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    documents: Mapped[list["UniversityDocument"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    scholarships: Mapped[list["UniversityScholarship"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    motivation_letters: Mapped[list["MotivationLetter"]] = relationship(back_populates="university")


class UniversityDocument(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Document catalog entry; the actual file remains on the original resource."""

    __tablename__ = "university_documents"
    __table_args__ = (
        UniqueConstraint("university_id", "subject_name", "title", name="uq_university_documents_subject_title"),
        Index("ix_university_documents_university_subject", "university_id", "subject_name"),
    )
    repr_fields = ("id", "university_id", "title")

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    university: Mapped[University] = relationship(back_populates="documents")


class UniversityScholarship(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "university_scholarships"
    __table_args__ = (Index("ix_university_scholarships_university_deadline", "university_id", "deadline"),)
    repr_fields = ("id", "university_id", "name")

    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    university: Mapped[University] = relationship(back_populates="scholarships")


class TuitionPrice(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Yearly tuition reference data, independent from application code."""

    __tablename__ = "tuition_prices"
    __table_args__ = (UniqueConstraint("country", "academic_year", name="uq_tuition_country_year"),)
    repr_fields = ("id", "country", "academic_year")

    country: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    academic_year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    tuition_in_state: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    tuition_out_of_state: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class EducationProgram(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "education_programs"
    __table_args__ = (Index("ix_education_programs_university_name", "university_id", "name"),)
    repr_fields = ("id", "name")

    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False)
    tuition_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    expected_start_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_growth_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    university: Mapped[University] = relationship(back_populates="programs")
    roi_calculations: Mapped[list["ROICalculation"]] = relationship(back_populates="program")


class SalaryStatistic(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "salary_statistics"
    __table_args__ = (Index("ix_salary_statistics_profession_country", "profession", "country"),)
    repr_fields = ("id", "profession", "country")

    profession: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    average_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    growth_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)


class CareerForecast(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "career_forecasts"
    __table_args__ = (Index("ix_career_forecasts_profession_year", "profession", "forecast_year"),)
    repr_fields = ("id", "profession", "forecast_year")

    profession: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    demand_score: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_growth_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    forecast_year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)


class CareerAnalysis(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """A persisted full career analysis, including anonymous trial analyses."""

    __tablename__ = "career_analyses"
    repr_fields = ("id", "university", "specialization")

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    university: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(500), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    study_years: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    living_costs_included: Mapped[bool] = mapped_column(nullable=False, server_default="false")

    education: Mapped["CareerEducation"] = relationship(
        back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )
    salary_forecast: Mapped["CareerSalaryForecast"] = relationship(
        back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )
    roi: Mapped["CareerROI"] = relationship(
        back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )
    scores: Mapped["CareerScores"] = relationship(
        back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )
    insights: Mapped[list["CareerInsight"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class CareerEducation(BaseIDMixin, db.Model):
    __tablename__ = "career_education"
    analysis_id: Mapped[int] = mapped_column(ForeignKey("career_analyses.id", ondelete="CASCADE"), unique=True)
    tuition_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tuition_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    learning_budget_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    learning_budget_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    investment_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    investment_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    analysis: Mapped[CareerAnalysis] = relationship(back_populates="education")


class CareerSalaryForecast(BaseIDMixin, db.Model):
    __tablename__ = "career_salary_forecasts"
    analysis_id: Mapped[int] = mapped_column(ForeignKey("career_analyses.id", ondelete="CASCADE"), unique=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    analysis: Mapped[CareerAnalysis] = relationship(back_populates="salary_forecast")
    bands: Mapped[list["CareerSalaryBand"]] = relationship(back_populates="forecast", cascade="all, delete-orphan")


class CareerSalaryBand(BaseIDMixin, db.Model):
    __tablename__ = "career_salary_bands"
    forecast_id: Mapped[int] = mapped_column(ForeignKey("career_salary_forecasts.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    monthly_min: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_max: Mapped[int] = mapped_column(Integer, nullable=False)
    realistic_target_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    realistic_target_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forecast: Mapped[CareerSalaryForecast] = relationship(back_populates="bands")


class CareerROI(BaseIDMixin, db.Model):
    __tablename__ = "career_roi"
    analysis_id: Mapped[int] = mapped_column(ForeignKey("career_analyses.id", ondelete="CASCADE"), unique=True)
    payback_likely: Mapped[bool] = mapped_column(nullable=False)
    probability_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    payback_months_min: Mapped[int] = mapped_column(Integer, nullable=False)
    payback_months_max: Mapped[int] = mapped_column(Integer, nullable=False)
    first_year_roi_min: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    first_year_roi_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    long_term_roi: Mapped[str] = mapped_column(String(20), nullable=False)
    analysis: Mapped[CareerAnalysis] = relationship(back_populates="roi")


class CareerScores(BaseIDMixin, db.Model):
    __tablename__ = "career_scores"
    analysis_id: Mapped[int] = mapped_column(ForeignKey("career_analyses.id", ondelete="CASCADE"), unique=True)
    career_potential: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    data_confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis: Mapped[CareerAnalysis] = relationship(back_populates="scores")


class CareerInsight(BaseIDMixin, db.Model):
    __tablename__ = "career_insights"
    __table_args__ = (Index("ix_career_insights_analysis_kind", "analysis_id", "kind"),)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("career_analyses.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[CareerAnalysis] = relationship(back_populates="insights")


class Partner(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Organization or person partnering with the project."""

    __tablename__ = "partners"
    __table_args__ = (Index("ix_partners_is_active_name", "is_active", "name"),)
    repr_fields = ("id", "name")

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")


class MotivationLetter(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """AI-generated or edited motivation letter belonging to a user."""

    __tablename__ = "motivation_letters"
    __table_args__ = (
        Index("ix_motivation_letters_user_status", "user_id", "status"),
    )
    repr_fields = ("id", "user_id", "title")

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    university_id: Mapped[int | None] = mapped_column(
        ForeignKey("universities.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generation_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", server_default="draft")
    ai_model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    user: Mapped[User] = relationship(back_populates="motivation_letters")
    university: Mapped[University | None] = relationship(back_populates="motivation_letters")

class ROICalculation(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "roi_calculations"
    __table_args__ = (
        Index("ix_roi_calculations_user_deleted_created", "user_id", "deleted_at", "created_at"),
        Index("ix_roi_calculations_program_deleted", "program_id", "deleted_at"),
    )
    repr_fields = ("id", "user_id", "program_id")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    program_id: Mapped[int | None] = mapped_column(
        ForeignKey("education_programs.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    roi_percent: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    break_even_months: Mapped[int] = mapped_column(Integer, nullable=False)
    study_years: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False, server_default="4")
    possible_monthly_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    methodology_version: Mapped[str] = mapped_column(String(30), nullable=False, server_default="v1")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    user: Mapped[User] = relationship(back_populates="roi_calculations")
    program: Mapped[EducationProgram | None] = relationship(back_populates="roi_calculations")


class UserRoadmap(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    __tablename__ = "user_roadmaps"
    __table_args__ = (Index("ix_user_roadmaps_user_updated", "user_id", "updated_at"),)
    repr_fields = ("id", "user_id", "target_job")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    target_job: Mapped[str] = mapped_column(String(255), nullable=False)
    dreamwork_plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    roadmap_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship(back_populates="roadmaps")


class SimulationScenario(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """User-owned decision scenario with immutable numbered revisions."""

    __tablename__ = "simulation_scenarios"
    __table_args__ = (Index("ix_simulation_scenarios_user_updated", "user_id", "updated_at"),)
    repr_fields = ("id", "user_id", "name", "current_revision_number")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", server_default="active")
    current_revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")

    user: Mapped[User] = relationship(back_populates="simulation_scenarios")
    revisions: Mapped[list["SimulationRevision"]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SimulationRevision.revision_number",
    )


class SimulationRevision(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Immutable input snapshot for a simulation scenario."""

    __tablename__ = "simulation_revisions"
    __table_args__ = (
        UniqueConstraint("scenario_id", "revision_number", name="uq_simulation_revision_number"),
        Index("ix_simulation_revisions_scenario_created", "scenario_id", "created_at"),
    )
    repr_fields = ("id", "scenario_id", "revision_number")

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_scenarios.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    assumptions: Mapped[dict] = mapped_column(JSON, nullable=False)
    methodology_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="scenario-foundation-v1", server_default="scenario-foundation-v1"
    )
    source_snapshot_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    change_note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    scenario: Mapped[SimulationScenario] = relationship(back_populates="revisions")
    projections: Mapped[list["SimulationProjection"]] = relationship(
        back_populates="revision",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SimulationProjection.created_at",
    )


class SimulationProjection(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Immutable deterministic financial result for one scenario revision."""

    __tablename__ = "simulation_projections"
    __table_args__ = (
        UniqueConstraint(
            "revision_id",
            "methodology_version",
            "input_fingerprint",
            name="uq_simulation_projection_input",
        ),
        Index("ix_simulation_projections_revision_created", "revision_id", "created_at"),
    )
    repr_fields = ("id", "revision_id", "methodology_version")

    revision_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_revisions.id", ondelete="CASCADE"), nullable=False
    )
    methodology_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    salary_basis: Mapped[str] = mapped_column(String(30), nullable=False)
    total_direct_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    opportunity_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_investment: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    estimated_start_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    calculation_inputs: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}"
    )
    cost_breakdown: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}"
    )
    payback_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payback_from_enrollment_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    break_even_reached: Mapped[bool] = mapped_column(Boolean, nullable=False)
    horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)
    cumulative_incremental_earnings: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    roi_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    salary_trajectory: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    evidence: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    source_snapshot_refs: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    unverified_assumptions: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    revision: Mapped[SimulationRevision] = relationship(back_populates="projections")


class MarketSnapshot(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Validated, deduplicated labour-market observation used by projections."""

    __tablename__ = "market_snapshots"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_market_snapshot_fingerprint"),
        Index(
            "ix_market_snapshots_lookup",
            "country",
            "role",
            "seniority",
            "currency",
            "snapshot_date",
        ),
    )
    repr_fields = ("id", "role", "country", "seniority", "snapshot_date")

    role: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    seniority: Mapped[str] = mapped_column(String(120), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    salary_basis: Mapped[str] = mapped_column(
        String(30), nullable=False, default="gross_annual", server_default="gross_annual"
    )
    salary_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    median_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    salary_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    vacancy_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    demand_index: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    sources: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="validated", server_default="validated"
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
