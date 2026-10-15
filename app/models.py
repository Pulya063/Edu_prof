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
    """Сценарій власника; summary відображає поточну ревізію, умови зберігаються окремо."""

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
    """Знімок умов: сервіс додає нову ревізію замість зміни вже збереженої."""

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
    """Компактний канонічний підсумок; деталі розкладені у пов'язані таблиці."""

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
    total_direct_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    opportunity_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_investment: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    estimated_start_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    # Окупність після випуску та від початку навчання; NULL означає, що її не досягнуто.
    payback_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payback_from_enrollment_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    break_even_reached: Mapped[bool] = mapped_column(Boolean, nullable=False)
    horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)
    cumulative_incremental_earnings: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    roi_percent: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    revision: Mapped[SimulationRevision] = relationship(back_populates="projections")
    inputs: Mapped["ProjectionInput"] = relationship(
        back_populates="projection", uselist=False, cascade="all, delete-orphan"
    )
    costs: Mapped["ProjectionCost"] = relationship(
        back_populates="projection", uselist=False, cascade="all, delete-orphan"
    )
    trajectory_points: Mapped[list["ProjectionTrajectoryPoint"]] = relationship(
        back_populates="projection", cascade="all, delete-orphan", order_by="ProjectionTrajectoryPoint.year"
    )
    evidence_records: Mapped[list["ProjectionEvidenceRecord"]] = relationship(
        back_populates="projection", cascade="all, delete-orphan", order_by="ProjectionEvidenceRecord.id"
    )
    source_records: Mapped[list["ProjectionSource"]] = relationship(
        back_populates="projection", cascade="all, delete-orphan", order_by="ProjectionSource.id"
    )
    warning_records: Mapped[list["ProjectionWarning"]] = relationship(
        back_populates="projection", cascade="all, delete-orphan", order_by="ProjectionWarning.id"
    )
    ai_review: Mapped["ProjectionAIReview | None"] = relationship(
        back_populates="projection", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def calculation_inputs(self) -> dict:
        return self.inputs.as_dict() if self.inputs else {}

    @property
    def cost_breakdown(self) -> dict:
        return self.costs.as_dict() if self.costs else {}

    @property
    def salary_trajectory(self) -> list[dict]:
        return [point.as_dict() for point in self.trajectory_points]

    @property
    def evidence(self) -> list[dict]:
        return [record.as_dict() for record in self.evidence_records]

    @property
    def source_snapshot_refs(self) -> list[str]:
        return [record.reference for record in self.source_records]

    @property
    def unverified_assumptions(self) -> list[str]:
        return [record.code for record in self.warning_records]


class ProjectionInput(db.Model):
    """Resolved numeric assumptions actually supplied to the deterministic engine."""

    __tablename__ = "projection_inputs"

    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), primary_key=True
    )
    annual_start_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    baseline_annual_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_salary_growth_percent: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    baseline_salary_growth_percent: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    foregone_income_percent: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    mandatory_fees: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    scholarships_and_grants: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    additional_education_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    incremental_living_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    employment_income_during_study: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)
    market_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_snapshots.id", ondelete="RESTRICT"), nullable=True
    )
    salary_source_kind: Mapped[str] = mapped_column(String(30), nullable=False)

    projection: Mapped[SimulationProjection] = relationship(back_populates="inputs")

    def as_dict(self) -> dict:
        return {
            "market_snapshot_id": self.market_snapshot_id,
            "annual_start_salary": self.annual_start_salary,
            "baseline_annual_salary": self.baseline_annual_salary,
            "annual_salary_growth_percent": self.annual_salary_growth_percent,
            "baseline_salary_growth_percent": self.baseline_salary_growth_percent,
            "foregone_income_percent": self.foregone_income_percent,
            "mandatory_fees": self.mandatory_fees,
            "scholarships_and_grants": self.scholarships_and_grants,
            "additional_education_cost": self.additional_education_cost,
            "incremental_living_cost": self.incremental_living_cost,
            "employment_income_during_study": self.employment_income_during_study,
            "horizon_years": self.horizon_years,
        }


class ProjectionCost(db.Model):
    """One-to-one auditable cost composition for a projection."""

    __tablename__ = "projection_costs"

    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), primary_key=True
    )
    tuition: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    mandatory_fees: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    additional_education: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    incremental_living_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    scholarships_and_grants: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    gross_direct_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_direct_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    baseline_income_during_study: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    employment_income_during_study: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    opportunity_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    projection: Mapped[SimulationProjection] = relationship(back_populates="costs")

    def as_dict(self) -> dict:
        return {
            "tuition": self.tuition,
            "mandatory_fees": self.mandatory_fees,
            "additional_education": self.additional_education,
            "incremental_living_cost": self.incremental_living_cost,
            "scholarships_and_grants": self.scholarships_and_grants,
            "gross_direct_cost": self.gross_direct_cost,
            "net_direct_cost": self.net_direct_cost,
            "baseline_income_during_study": self.baseline_income_during_study,
            "employment_income_during_study": self.employment_income_during_study,
            "opportunity_cost": self.opportunity_cost,
        }


class ProjectionTrajectoryPoint(db.Model):
    __tablename__ = "projection_trajectory_points"
    __table_args__ = (UniqueConstraint("projection_id", "year", name="uq_projection_trajectory_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    target_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    baseline_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    incremental_earnings: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cumulative_incremental_earnings: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)

    projection: Mapped[SimulationProjection] = relationship(back_populates="trajectory_points")

    def as_dict(self) -> dict:
        return {
            "year": self.year,
            "target_salary": self.target_salary,
            "baseline_salary": self.baseline_salary,
            "incremental_earnings": self.incremental_earnings,
            "cumulative_incremental_earnings": self.cumulative_incremental_earnings,
        }


class ProjectionEvidenceRecord(db.Model):
    __tablename__ = "projection_evidence"
    __table_args__ = (Index("ix_projection_evidence_projection_metric", "projection_id", "metric"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(1000), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    seniority: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)

    projection: Mapped[SimulationProjection] = relationship(back_populates="evidence_records")

    def as_dict(self) -> dict:
        return {
            "metric": self.metric,
            "source_name": self.source_name,
            "source_reference": self.source_reference,
            "acquired_at": self.acquired_at,
            "country": self.country,
            "role": self.role,
            "seniority": self.seniority,
            "currency": self.currency,
            "sample_size": self.sample_size,
            "confidence": self.confidence,
        }


class ProjectionSource(db.Model):
    __tablename__ = "projection_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=False)
    market_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_snapshots.id", ondelete="RESTRICT"), nullable=True
    )
    tuition_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("tuition_snapshots.id", ondelete="RESTRICT"), nullable=True
    )

    projection: Mapped[SimulationProjection] = relationship(back_populates="source_records")


class ProjectionWarning(db.Model):
    __tablename__ = "projection_warnings"
    __table_args__ = (UniqueConstraint("projection_id", "code", name="uq_projection_warning_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)

    projection: Mapped[SimulationProjection] = relationship(back_populates="warning_records")


class ProjectionAIReview(TimestampMixin, db.Model):
    """Advisory Deep Agent review; it never overwrites deterministic financial fields."""

    __tablename__ = "projection_ai_reviews"
    __table_args__ = (UniqueConstraint("projection_id", name="uq_projection_ai_review_projection"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    projection_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_projections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", server_default="pending")
    provider_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    ai_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calculation_consistent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    prediction_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    verdict: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    suggested_adjustments: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    projection: Mapped[SimulationProjection] = relationship(back_populates="ai_review")


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


class TuitionSnapshot(BaseIDMixin, TimestampMixin, ReprMixin, db.Model):
    """Збережене джерело tuition для чинного resolver; ingestion відокремлений від розрахунку."""

    __tablename__ = "tuition_snapshots"
    __table_args__ = (
        UniqueConstraint("fingerprint", name="uq_tuition_snapshot_fingerprint"),
        Index(
            "ix_tuition_snapshots_lookup",
            "country",
            "university",
            "program",
            "degree",
            "currency",
            "snapshot_date",
        ),
    )
    repr_fields = ("id", "scope", "country", "university", "program", "snapshot_date")

    scope: Mapped[str] = mapped_column(String(30), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    university: Mapped[str | None] = mapped_column(String(255), nullable=True)
    program: Mapped[str | None] = mapped_column(String(500), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    study_mode: Mapped[str | None] = mapped_column(String(80), nullable=True)
    student_residency: Mapped[str] = mapped_column(
        String(40), nullable=False, default="unspecified", server_default="unspecified"
    )
    institution_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    annual_tuition_min: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_tuition: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_tuition_max: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mandatory_fees: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    sources: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="validated", server_default="validated"
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
