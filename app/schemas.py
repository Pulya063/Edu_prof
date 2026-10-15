from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator, model_validator

T = TypeVar("T")


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    # Optional for API clients, accepted for the web form and validated when sent.
    confirm_password: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Пароль повинен містити не менше 8 символів")
        if not any(char.isupper() for char in value):
            raise ValueError("Пароль повинен містити хоча б одну велику літеру")
        if not any(char.islower() for char in value):
            raise ValueError("Пароль повинен містити хоча б одну маленьку літеру")
        if not any(char.isdigit() for char in value):
            raise ValueError("Пароль повинен містити хоча б одну цифру")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterSchema":
        if self.confirm_password is not None and self.password != self.confirm_password:
            raise ValueError("Паролі не співпадають")
        return self


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPairResponse(BaseModel):
    """Returned on login/register — contains both access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"










class ROICalculationRequest(BaseModel):
    """Legacy anonymous trial inputs; versioned simulations use SimulationCreateRequest."""

    model_config = ConfigDict(extra="forbid")

    university: str = Field(min_length=2, max_length=255)
    faculty: str = Field(min_length=2, max_length=255)
    annual_tuition: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    study_years: Decimal = Field(default=Decimal("4"), ge=Decimal("1"), le=Decimal("12"), decimal_places=1)


class TrialROIRequest(ROICalculationRequest):
    """Four-field input accepted by the anonymous trial endpoint."""
    university: str = Field(default="Demo University", min_length=2, max_length=255)
    faculty: str = Field(default="Computer Science", min_length=2, max_length=255)
    annual_tuition: Decimal = Field(default=Decimal("15000.00"), gt=Decimal("0"), max_digits=14, decimal_places=2)
    study_years: Decimal = Field(default=Decimal("4"), ge=Decimal("1"), le=Decimal("12"), decimal_places=1)


class TrialMinimumMoney(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float = Field(ge=0, allow_inf_nan=False)


class TrialMinimumMonths(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: int = Field(ge=1)


class TrialMinimumPercent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: float = Field(allow_inf_nan=False)


class TrialEducationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specialization: str = Field(min_length=2, max_length=500)
    total_investment: TrialMinimumMoney
    total_education_cost: TrialMinimumMoney


class TrialROIResultResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payback_months: TrialMinimumMonths
    first_year_roi_percent: TrialMinimumPercent
    roi_percent: TrialMinimumPercent


class TrialROIResponse(BaseModel):
    """Validated abbreviated result returned by the anonymous trial endpoint."""

    model_config = ConfigDict(extra="forbid")

    education: TrialEducationResponse
    roi: TrialROIResultResponse


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: T | None = None








class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetSchema(BaseModel):
    code: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not any(char.isupper() for char in value):
            raise ValueError("Пароль повинен містити хоча б одну велику літеру")
        if not any(char.islower() for char in value):
            raise ValueError("Пароль повинен містити хоча б одну маленьку літеру")
        if not any(char.isdigit() for char in value):
            raise ValueError("Пароль повинен містити хоча б одну цифру")
        return value


class SimulationAssumptions(BaseModel):
    """Вхідні умови освіти й кар'єри; після вибору tuition зберігаються в ревізії."""

    model_config = ConfigDict(extra="forbid")

    university: str = Field(min_length=2, max_length=255)
    specialization: str = Field(min_length=2, max_length=500)
    country: str = Field(min_length=2, max_length=120)
    degree: str = Field(min_length=2, max_length=255)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    # None означає вибір snapshot; 0 є явною вартістю безкоштовного навчання.
    annual_tuition: Decimal | None = Field(default=None, ge=Decimal("0"), max_digits=14, decimal_places=2)
    study_duration_years: Decimal = Field(gt=Decimal("0"), le=Decimal("12"), decimal_places=1)
    career_target: str = Field(min_length=2, max_length=255)
    existing_skills: list[str] = Field(default_factory=list, max_length=100)
    additional_education: list[str] = Field(default_factory=list, max_length=50)
    courses: list[str] = Field(default_factory=list, max_length=100)
    certifications: list[str] = Field(default_factory=list, max_length=100)
    experience_years: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("60"), decimal_places=1)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class TuitionSnapshotSelection(BaseModel):
    """Пошук збереженої ціни: точність, давність і довіра; без live API викликів."""
    model_config = ConfigDict(extra="forbid")

    university: str = Field(min_length=2, max_length=255)
    program: str = Field(min_length=2, max_length=500)
    country: str = Field(min_length=2, max_length=120)
    degree: str | None = Field(default=None, min_length=2, max_length=255)
    study_mode: str | None = Field(default=None, min_length=2, max_length=80)
    student_residency: Literal[
        "domestic", "international", "eu", "non_eu", "in_state", "out_of_state", "unspecified"
    ] = "unspecified"
    institution_type: Literal["public", "private", "other"] | None = None
    currency: str = Field(min_length=3, max_length=3)
    as_of_date: date = Field(default_factory=date.today)
    max_age_days: int = Field(default=730, ge=1, le=3650)
    minimum_confidence: Literal["low", "medium", "high"] = "medium"
    allow_country_fallback: bool = False

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class CollegeScorecardTuitionRefreshRequest(BaseModel):
    """Queue an official institution-level tuition refresh for one UNITID."""

    model_config = ConfigDict(extra="forbid")

    scorecard_id: int = Field(gt=0)


class TuitionRefreshAcceptedResponse(BaseModel):
    job_id: str
    provider: Literal["college_scorecard"] = "college_scorecard"
    status: Literal["queued"] = "queued"


class SimulationCreateRequest(BaseModel):
    """Створення сценарію: ручна ціна або одне джерело tuition, без змішування."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=255)
    assumptions: SimulationAssumptions
    tuition_snapshot_id: int | None = Field(default=None, ge=1)
    tuition_snapshot_selection: TuitionSnapshotSelection | None = None

    @model_validator(mode="after")
    def select_tuition_source(self) -> "SimulationCreateRequest":
        source_count = sum(
            source is not None
            for source in (self.tuition_snapshot_id, self.tuition_snapshot_selection)
        )
        if source_count > 1:
            raise ValueError("Вкажіть лише одне tuition snapshot source")
        if source_count == 0 and self.assumptions.annual_tuition is None:
            raise ValueError("Вкажіть annual_tuition або tuition snapshot source")
        if source_count == 1 and self.assumptions.annual_tuition is not None:
            raise ValueError("Не поєднуйте manual annual_tuition з tuition snapshot source")
        return self


class SimulationRevisionCreateRequest(BaseModel):
    """Новий повний набір умов; попередню ревізію та її прогнози не переписуємо."""
    model_config = ConfigDict(extra="forbid")
    assumptions: SimulationAssumptions
    change_note: str | None = Field(default=None, max_length=500)
    tuition_snapshot_id: int | None = Field(default=None, ge=1)
    tuition_snapshot_selection: TuitionSnapshotSelection | None = None

    @model_validator(mode="after")
    def select_tuition_source(self) -> "SimulationRevisionCreateRequest":
        source_count = sum(
            source is not None
            for source in (self.tuition_snapshot_id, self.tuition_snapshot_selection)
        )
        if source_count > 1:
            raise ValueError("Вкажіть лише одне tuition snapshot source")
        if source_count == 0 and self.assumptions.annual_tuition is None:
            raise ValueError("Вкажіть annual_tuition або tuition snapshot source")
        if source_count == 1 and self.assumptions.annual_tuition is not None:
            raise ValueError("Не поєднуйте manual annual_tuition з tuition snapshot source")
        return self


class SimulationRevisionResponse(BaseModel):
    """Збережені умови й посилання на джерела для відтворення рішення."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    revision_number: int
    assumptions: SimulationAssumptions
    methodology_version: str
    source_snapshot_refs: list[str]
    change_note: str | None
    created_at: datetime


class SimulationScenarioSummary(BaseModel):
    """Короткий запис для списків; фінансові результати читаються окремо."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: str
    current_revision_number: int
    target_role: str
    country: str
    currency: str
    created_at: datetime
    updated_at: datetime


class SimulationScenarioResponse(SimulationScenarioSummary):
    """Сценарій разом з історією його умов, а не лише поточними значеннями."""
    revisions: list[SimulationRevisionResponse]


class ProjectionEvidence(BaseModel):
    """Походження конкретного показника; валідна форма не підтверджує правдивість джерела."""
    model_config = ConfigDict(extra="forbid")

    metric: Literal[
        "target_start_salary",
        "baseline_salary",
        "salary_growth",
        "tuition",
        "mandatory_fees",
        "scholarships",
        "study_income",
    ]
    source_name: str = Field(min_length=2, max_length=255)
    source_reference: str = Field(min_length=2, max_length=1000)
    acquired_at: datetime
    country: str = Field(min_length=2, max_length=120)
    role: str = Field(min_length=2, max_length=255)
    seniority: str = Field(min_length=2, max_length=120)
    currency: str = Field(min_length=3, max_length=3)
    sample_size: int | None = Field(default=None, ge=1)
    confidence: Literal["low", "medium", "high"]

    @field_validator("currency")
    @classmethod
    def normalize_evidence_currency(cls, value: str) -> str:
        return value.upper()


class MarketSnapshotSelection(BaseModel):
    """Explicit, auditable policy for resolving one validated market snapshot."""

    model_config = ConfigDict(extra="forbid")

    seniority: str = Field(min_length=2, max_length=120)
    as_of_date: date = Field(default_factory=date.today)
    max_age_days: int = Field(default=365, ge=1, le=3650)
    minimum_confidence: Literal["low", "medium", "high"] = "medium"

    @field_validator("seniority")
    @classmethod
    def normalize_seniority(cls, value: str) -> str:
        return value.strip().casefold()


class SimulationProjectionRequest(BaseModel):
    """Умови фінансового прогнозу: рівно одне джерело зарплати та явний baseline."""
    model_config = ConfigDict(extra="forbid")

    market_snapshot_id: int | None = Field(default=None, ge=1)
    market_snapshot_selection: MarketSnapshotSelection | None = None
    annual_start_salary: Decimal | None = Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2)
    baseline_annual_salary: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    annual_salary_growth_percent: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("50"))
    baseline_salary_growth_percent: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("50"))
    foregone_income_percent: Decimal = Field(default=Decimal("100"), ge=Decimal("0"), le=Decimal("100"))
    # Додаткові витрати та гранти — суми за весь період навчання, не річні платежі.
    mandatory_fees: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    scholarships_and_grants: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    additional_education_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    incremental_living_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    employment_income_during_study: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=14,
        decimal_places=2,
        description="Optional total gross income earned during the full study period.",
    )
    horizon_years: int = Field(default=10, ge=1, le=30)
    evidence: list[ProjectionEvidence] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def select_salary_source(self) -> "SimulationProjectionRequest":
        source_count = sum(
            source is not None
            for source in (
                self.market_snapshot_id,
                self.market_snapshot_selection,
                self.annual_start_salary,
            )
        )
        if source_count != 1:
            raise ValueError(
                "Вкажіть рівно одне джерело зарплати: market_snapshot_id, "
                "market_snapshot_selection або annual_start_salary"
            )
        return self


class SalaryTrajectoryPoint(BaseModel):
    """Рік після навчання: дохід цільового шляху мінус альтернативний дохід."""
    year: int
    target_salary: Decimal
    baseline_salary: Decimal
    incremental_earnings: Decimal
    cumulative_incremental_earnings: Decimal


class ProjectionCostBreakdown(BaseModel):
    """Detailed v2 breakdown; fields stay optional for readable v1 history."""

    tuition: Decimal | None = None
    mandatory_fees: Decimal | None = None
    additional_education: Decimal | None = None
    incremental_living_cost: Decimal | None = None
    scholarships_and_grants: Decimal | None = None
    gross_direct_cost: Decimal | None = None
    net_direct_cost: Decimal | None = None
    baseline_income_during_study: Decimal | None = None
    employment_income_during_study: Decimal | None = None
    opportunity_cost: Decimal | None = None


class ProjectionAIReviewResponse(BaseModel):
    """Advisory AI review stored separately from canonical financial numbers."""

    model_config = ConfigDict(from_attributes=True)

    status: Literal["pending", "running", "completed", "failed", "not_configured"]
    provider_model: str | None = None
    confidence_score: Decimal | None = None
    ai_risk_score: int | None = None
    calculation_consistent: bool | None = None
    prediction_summary: str | None = None
    verdict: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_adjustments: list[dict] = Field(default_factory=list)
    error_message: str | None = None
    completed_at: datetime | None = None


class SimulationProjectionResponse(BaseModel):
    """Збережений deterministic результат із методологією, входами й обмеженнями."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    revision_id: int
    methodology_version: str
    input_fingerprint: str
    currency: str
    salary_basis: str
    total_direct_cost: Decimal
    opportunity_cost: Decimal
    total_investment: Decimal
    estimated_start_salary: Decimal
    calculation_inputs: dict
    cost_breakdown: ProjectionCostBreakdown
    # None: окупності немає в межах горизонту; 0: інвестиція дорівнює нулю.
    # Перший показник рахується після випуску, другий — від початку навчання.
    payback_months: int | None
    payback_from_enrollment_months: int | None
    break_even_reached: bool
    horizon_years: int
    cumulative_incremental_earnings: Decimal
    roi_percent: Decimal | None
    salary_trajectory: list[SalaryTrajectoryPoint]
    evidence: list[ProjectionEvidence]
    source_snapshot_refs: list[str]
    unverified_assumptions: list[str]
    ai_review: ProjectionAIReviewResponse | None = None
    created_at: datetime


class MarketSnapshotSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=255)
    reference: str = Field(min_length=2, max_length=1000)
    url: HttpUrl | None = None
    acquired_at: datetime

    @field_validator("acquired_at")
    @classmethod
    def require_source_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("acquired_at має містити timezone")
        return value


class MarketSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=2, max_length=255)
    country: str = Field(min_length=2, max_length=120)
    seniority: str = Field(min_length=2, max_length=120)
    snapshot_date: date
    currency: str = Field(min_length=3, max_length=3)
    salary_min: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    median_salary: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    salary_max: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    vacancy_count: int | None = Field(default=None, ge=0)
    demand_index: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
    sources: list[MarketSnapshotSource] = Field(min_length=1, max_length=20)
    acquired_at: datetime
    sample_size: int | None = Field(default=None, ge=1)
    confidence: Literal["low", "medium", "high"]
    methodology_version: str = Field(min_length=2, max_length=50)

    @field_validator("currency")
    @classmethod
    def normalize_snapshot_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_salary_range(self) -> "MarketSnapshotCreateRequest":
        if not self.salary_min <= self.median_salary <= self.salary_max:
            raise ValueError("Salary range має відповідати salary_min <= median_salary <= salary_max")
        if self.acquired_at.tzinfo is None or self.acquired_at.utcoffset() is None:
            raise ValueError("acquired_at має містити timezone")
        if self.snapshot_date > self.acquired_at.date():
            raise ValueError("snapshot_date не може бути пізніше acquired_at")
        return self


class MarketSnapshotQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str | None = Field(default=None, min_length=2, max_length=255)
    country: str | None = Field(default=None, min_length=2, max_length=120)
    seniority: str | None = Field(default=None, min_length=2, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("currency")
    @classmethod
    def normalize_query_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class MarketSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    country: str
    seniority: str
    snapshot_date: date
    currency: str
    salary_basis: str
    salary_min: Decimal
    median_salary: Decimal
    salary_max: Decimal
    vacancy_count: int | None
    demand_index: Decimal | None
    sources: list[MarketSnapshotSource]
    acquired_at: datetime
    sample_size: int | None
    confidence: str
    methodology_version: str
    validation_status: str
    fingerprint: str
    created_at: datetime


class TuitionSnapshotSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=255)
    reference: str = Field(min_length=2, max_length=1000)
    url: HttpUrl | None = None
    acquired_at: datetime

    @field_validator("acquired_at")
    @classmethod
    def require_source_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("acquired_at має містити timezone")
        return value


class TuitionSnapshotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: Literal["program", "university", "country_average"]
    country: str = Field(min_length=2, max_length=120)
    university: str | None = Field(default=None, min_length=2, max_length=255)
    program: str | None = Field(default=None, min_length=2, max_length=500)
    degree: str | None = Field(default=None, min_length=2, max_length=255)
    study_mode: str | None = Field(default=None, min_length=2, max_length=80)
    student_residency: Literal[
        "domestic", "international", "eu", "non_eu", "in_state", "out_of_state", "unspecified"
    ] = "unspecified"
    institution_type: Literal["public", "private", "other"] | None = None
    academic_year: str = Field(min_length=4, max_length=20)
    snapshot_date: date
    currency: str = Field(min_length=3, max_length=3)
    annual_tuition_min: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    annual_tuition: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    annual_tuition_max: Decimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    mandatory_fees: Decimal | None = Field(default=None, ge=Decimal("0"), max_digits=14, decimal_places=2)
    sources: list[TuitionSnapshotSource] = Field(min_length=1, max_length=20)
    acquired_at: datetime
    confidence: Literal["low", "medium", "high"]
    methodology_version: str = Field(min_length=2, max_length=50)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_snapshot(self) -> "TuitionSnapshotCreateRequest":
        if not self.annual_tuition_min <= self.annual_tuition <= self.annual_tuition_max:
            raise ValueError(
                "Tuition range має відповідати annual_tuition_min <= annual_tuition <= annual_tuition_max"
            )
        if self.acquired_at.tzinfo is None or self.acquired_at.utcoffset() is None:
            raise ValueError("acquired_at має містити timezone")
        if self.snapshot_date > self.acquired_at.date():
            raise ValueError("snapshot_date не може бути пізніше acquired_at")
        if self.scope == "program" and (not self.university or not self.program):
            raise ValueError("Program snapshot потребує university і program")
        if self.scope == "university" and not self.university:
            raise ValueError("University snapshot потребує university")
        if self.scope == "country_average" and (self.university or self.program):
            raise ValueError("Country average не повинен містити university або program")
        return self


class TuitionSnapshotQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str | None = Field(default=None, min_length=2, max_length=120)
    university: str | None = Field(default=None, min_length=2, max_length=255)
    program: str | None = Field(default=None, min_length=2, max_length=500)
    degree: str | None = Field(default=None, min_length=2, max_length=255)
    scope: Literal["program", "university", "country_average"] | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class TuitionSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scope: str
    country: str
    university: str | None
    program: str | None
    degree: str | None
    study_mode: str | None
    student_residency: str
    institution_type: str | None
    academic_year: str
    snapshot_date: date
    currency: str
    annual_tuition_min: Decimal
    annual_tuition: Decimal
    annual_tuition_max: Decimal
    mandatory_fees: Decimal | None
    sources: list[TuitionSnapshotSource]
    acquired_at: datetime
    confidence: str
    methodology_version: str
    validation_status: str
    fingerprint: str
    created_at: datetime


class ProjectionSnapshotProvenance(BaseModel):
    snapshot: MarketSnapshotResponse
    age_days: int = Field(ge=0)
    selected_metric: Literal["median_salary"] = "median_salary"
    selected_value: Decimal


class SimulationProjectionExplainabilityResponse(BaseModel):
    """Джерела зарплати й обмеження збереженого прогнозу без нового розрахунку."""
    projection_id: int
    calculation_type: Literal["deterministic"] = "deterministic"
    ai_generated: Literal[False] = False
    methodology_version: str
    salary_basis: str
    currency: str
    salary_source_kind: Literal["market_snapshot", "manual_evidence"]
    selected_salary_metric: Literal["median_salary", "annual_start_salary"]
    estimated_start_salary: Decimal
    source_snapshots: list[ProjectionSnapshotProvenance]
    source_integrity: Literal["complete", "missing"]
    missing_source_snapshot_refs: list[str]
    evidence: list[ProjectionEvidence]
    unverified_assumptions: list[str]


class SimulationOverviewResponse(BaseModel):
    """Стан звіту: сценаріїв немає, є лише умови або вже є фінансовий прогноз."""
    status: Literal["empty", "scenario_only", "projected"]
    scenario: SimulationScenarioResponse | None = None
    projection: SimulationProjectionResponse | None = None
    explainability: SimulationProjectionExplainabilityResponse | None = None


class RoadmapGenerateRequest(BaseModel):
    target_job: str = Field(min_length=2, max_length=255)
    hours_per_week: int = Field(default=10, ge=1, le=168)
    current_income: float = Field(default=0.0, ge=0.0)
    skills: list[str] = Field(default_factory=list)


class UserRoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_job: str
    dreamwork_plan_id: int | None
    roadmap_data: dict


class WorkspaceProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_of_study: str = Field(default="Computer Science", min_length=2, max_length=255)
    country: str = Field(default="Poland", min_length=2, max_length=120)
    about: str = Field(default="", max_length=300)
    skills: list[str] = Field(default_factory=list, max_length=100)
    career_target: str | None = Field(default=None, max_length=255)


class WorkspacePreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Literal["English", "Українська"] = "English"
    currency: Literal["USD", "EUR", "PLN", "GBP"] = "USD"
    theme: Literal["Fence default"] = "Fence default"


class WorkspaceProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=2, max_length=50)
    profile: WorkspaceProfile


class WorkspaceStateResponse(BaseModel):
    user: dict[str, Any]
    profile: WorkspaceProfile
    preferences: WorkspacePreferences
    connections: dict[str, dict[str, Any]]
    saved_course_ids: list[str]
    roadmap: dict[str, Any] | None


class WorkspaceCourseResponse(BaseModel):
    id: str
    title: str
    description: str
    level: str
    language: str
    format: str
    duration: str
    skills: list[str]
    provider_name: str
    provider_url: str | None = None
    saved: bool = False


class WorkspaceResourceResponse(BaseModel):
    id: str
    title: str
    description: str
    source: Literal["Public web", "YouTube"]
    url: str
    skills: list[str]


class WorkspaceUniversityResponse(BaseModel):
    id: str
    name: str
    country: str
    city: str | None = None
    website: str | None = None
    description: str
    annual_tuition: float | None = None
    currency: str = "EUR"
    duration_years: float | None = None
    study_mode: str = "Full-time"
    program_name: str
    data_quality: Literal["database", "illustrative"]


class WorkspaceUniversityDetailsResponse(WorkspaceUniversityResponse):
    programmes: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    scholarships: list[dict[str, Any]] = Field(default_factory=list)


class RoadmapPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_job: str = Field(min_length=2, max_length=255)
    current_level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    hours_per_week: int = Field(default=8, ge=1, le=80)
    skills: list[str] = Field(default_factory=list, max_length=100)


class RoadmapTaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool
