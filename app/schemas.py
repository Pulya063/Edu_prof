from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, PlainSerializer, field_validator, model_validator

T = TypeVar("T")

# Money, salaries and percentages: exact Decimal for the arithmetic, a plain JSON number on the wire.
ApiDecimal = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


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










class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: T | None = None








class AuthPlanLimits(BaseModel):
    roi_calculations: int | None
    roadmaps: int | None


class AuthUsage(BaseModel):
    roi_calculations: int
    roadmaps: int


class AuthMeResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    plan: str
    plan_limits: AuthPlanLimits
    plan_features: list[str]
    usage: AuthUsage
    calculations_remaining: int | None
    is_admin: bool = False


class AuthProviderStatus(BaseModel):
    configured: bool


class AuthProvidersResponse(BaseModel):
    google: AuthProviderStatus


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
    annual_tuition: ApiDecimal | None = Field(default=None, ge=Decimal("0"), max_digits=14, decimal_places=2)
    study_duration_years: ApiDecimal = Field(gt=Decimal("0"), le=Decimal("12"), decimal_places=1)
    career_target: str = Field(min_length=2, max_length=255)
    existing_skills: list[str] = Field(default_factory=list, max_length=100)
    additional_education: list[str] = Field(default_factory=list, max_length=50)
    courses: list[str] = Field(default_factory=list, max_length=100)
    certifications: list[str] = Field(default_factory=list, max_length=100)
    experience_years: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("60"), decimal_places=1)

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


class SimulationScenarioListItem(SimulationScenarioSummary):
    """Рядок списку: умови поточної ревізії та числа останнього прогнозу; без прогнозу числа порожні."""
    university: str | None = None
    specialization: str | None = None
    degree: str | None = None
    study_duration_years: ApiDecimal | None = None
    annual_tuition: ApiDecimal | None = None
    projection_id: int | None = None
    total_investment: ApiDecimal | None = None
    roi_percent: ApiDecimal | None = None
    payback_months: int | None = None


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
        "inflation",
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
    annual_start_salary: ApiDecimal | None = Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2)
    baseline_annual_salary: ApiDecimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    annual_salary_growth_percent: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("50"))
    baseline_salary_growth_percent: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("50"))
    foregone_income_percent: ApiDecimal = Field(default=Decimal("100"), ge=Decimal("0"), le=Decimal("100"))
    # Додаткові витрати та гранти — суми за весь період навчання, не річні платежі.
    mandatory_fees: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    scholarships_and_grants: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    additional_education_cost: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    incremental_living_cost: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    employment_income_during_study: ApiDecimal | None = Field(
        default=None,
        ge=Decimal("0"),
        max_digits=14,
        decimal_places=2,
        description="Optional total gross income earned during the full study period.",
    )
    horizon_years: int = Field(default=10, ge=1, le=30)
    # Optional: without a discount rate NPV is not calculated (null), never guessed.
    discount_rate_percent: ApiDecimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("30"))
    # v4 realism inputs. Inflation turns nominal growth into today's money; without it results stay nominal.
    inflation_percent: ApiDecimal | None = Field(default=None, ge=Decimal("-10"), le=Decimal("100"))
    job_search_months: int = Field(default=0, ge=0, le=24)
    employment_probability_percent: ApiDecimal = Field(default=Decimal("100"), ge=Decimal("1"), le=Decimal("100"))
    # v5: optional "should pay back within N years after graduation" target; must fit inside the horizon.
    target_payback_years: int | None = Field(default=None, ge=1, le=30)
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
        if self.target_payback_years is not None and self.target_payback_years > self.horizon_years:
            raise ValueError("Термін окупності не може перевищувати горизонт прогнозу")
        return self


class SalaryTrajectoryPoint(BaseModel):
    """Рік після навчання: дохід цільового шляху мінус альтернативний дохід."""
    year: int
    target_salary: ApiDecimal
    baseline_salary: ApiDecimal
    incremental_earnings: ApiDecimal
    cumulative_incremental_earnings: ApiDecimal


class ProjectionCostBreakdown(BaseModel):
    """Detailed v2 breakdown; fields stay optional for readable v1 history."""

    tuition: ApiDecimal | None = None
    mandatory_fees: ApiDecimal | None = None
    additional_education: ApiDecimal | None = None
    incremental_living_cost: ApiDecimal | None = None
    scholarships_and_grants: ApiDecimal | None = None
    gross_direct_cost: ApiDecimal | None = None
    net_direct_cost: ApiDecimal | None = None
    baseline_income_during_study: ApiDecimal | None = None
    employment_income_during_study: ApiDecimal | None = None
    opportunity_cost: ApiDecimal | None = None


class ProjectionAIReviewResponse(BaseModel):
    """Advisory AI review stored separately from canonical financial numbers."""

    model_config = ConfigDict(from_attributes=True)

    status: Literal["pending", "running", "completed", "failed", "not_configured"]
    provider_model: str | None = None
    confidence_score: ApiDecimal | None = None
    ai_risk_score: int | None = None
    calculation_consistent: bool | None = None
    prediction_summary: str | None = None
    verdict: str | None = None
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_adjustments: list[dict] = Field(default_factory=list)
    error_message: str | None = None
    completed_at: datetime | None = None


class ProjectionCalculationInputs(BaseModel):
    """Збережені входи розрахунку. Порожні для старих проєкцій без рядка projection_inputs."""
    market_snapshot_id: int | None = None
    annual_start_salary: ApiDecimal | None = None
    baseline_annual_salary: ApiDecimal | None = None
    annual_salary_growth_percent: ApiDecimal | None = None
    baseline_salary_growth_percent: ApiDecimal | None = None
    foregone_income_percent: ApiDecimal | None = None
    mandatory_fees: ApiDecimal | None = None
    scholarships_and_grants: ApiDecimal | None = None
    additional_education_cost: ApiDecimal | None = None
    incremental_living_cost: ApiDecimal | None = None
    employment_income_during_study: ApiDecimal | None = None
    horizon_years: int | None = None
    discount_rate_percent: ApiDecimal | None = None
    inflation_percent: ApiDecimal | None = None
    job_search_months: int | None = None
    employment_probability_percent: ApiDecimal | None = None
    target_payback_years: int | None = None


class ProjectionScenarioOutcome(BaseModel):
    """v3: one start-salary scenario on the same costs, growth and baseline."""
    scenario: Literal["pessimistic", "base", "optimistic"]
    start_salary: ApiDecimal
    cumulative_incremental_earnings: ApiDecimal
    roi_percent: ApiDecimal | None
    payback_months: int | None
    break_even_reached: bool
    npv: ApiDecimal | None = None


class SimulationProjectionResponse(BaseModel):
    """Збережений deterministic результат із методологією, входами й обмеженнями."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    revision_id: int
    methodology_version: str
    input_fingerprint: str
    currency: str
    salary_basis: str
    total_direct_cost: ApiDecimal
    opportunity_cost: ApiDecimal
    total_investment: ApiDecimal
    estimated_start_salary: ApiDecimal
    calculation_inputs: ProjectionCalculationInputs
    cost_breakdown: ProjectionCostBreakdown
    # None: окупності немає в межах горизонту; 0: інвестиція дорівнює нулю.
    # Перший показник рахується після випуску, другий — від початку навчання.
    payback_months: int | None
    payback_from_enrollment_months: int | None
    break_even_reached: bool
    # v5: null when no target was chosen; the gap is payback minus the target in months (negative = early).
    target_payback_years: int | None = None
    payback_within_target: bool | None = None
    payback_target_gap_months: int | None = None
    horizon_years: int
    cumulative_incremental_earnings: ApiDecimal
    roi_percent: ApiDecimal | None
    # v3 only: null without a discount rate; empty scenario list for older projections.
    npv: ApiDecimal | None = None
    scenario_outcomes: list[ProjectionScenarioOutcome] = Field(default_factory=list)
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
    salary_min: ApiDecimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    median_salary: ApiDecimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    salary_max: ApiDecimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    vacancy_count: int | None = Field(default=None, ge=0)
    demand_index: ApiDecimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("100"))
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
    salary_min: ApiDecimal
    median_salary: ApiDecimal
    salary_max: ApiDecimal
    vacancy_count: int | None
    demand_index: ApiDecimal | None
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
    annual_tuition_min: ApiDecimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    annual_tuition: ApiDecimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    annual_tuition_max: ApiDecimal = Field(ge=Decimal("0"), max_digits=14, decimal_places=2)
    mandatory_fees: ApiDecimal | None = Field(default=None, ge=Decimal("0"), max_digits=14, decimal_places=2)
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
    annual_tuition_min: ApiDecimal
    annual_tuition: ApiDecimal
    annual_tuition_max: ApiDecimal
    mandatory_fees: ApiDecimal | None
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
    selected_value: ApiDecimal


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
    estimated_start_salary: ApiDecimal
    source_snapshots: list[ProjectionSnapshotProvenance]
    source_integrity: Literal["complete", "missing"]
    missing_source_snapshot_refs: list[str]
    evidence: list[ProjectionEvidence]
    unverified_assumptions: list[str]


class RecentCalculationSummary(BaseModel):
    """Рядок дашборду: сценарій і підсумок його останнього прогнозу поточної ревізії, якщо він є."""
    scenario_id: int
    name: str
    status: str
    target_role: str
    country: str
    currency: str
    revision_number: int
    updated_at: datetime
    projection_id: int | None = None
    methodology_version: str | None = None
    total_investment: ApiDecimal | None = None
    roi_percent: ApiDecimal | None = None
    payback_months: int | None = None
    break_even_reached: bool | None = None
    horizon_years: int | None = None


class SimulationOverviewResponse(BaseModel):
    """Стан звіту: сценаріїв немає, є лише умови або вже є фінансовий прогноз."""
    status: Literal["empty", "scenario_only", "projected"]
    scenario: SimulationScenarioResponse | None = None
    projection: SimulationProjectionResponse | None = None
    explainability: SimulationProjectionExplainabilityResponse | None = None
    recent_calculations: list[RecentCalculationSummary] = Field(default_factory=list)


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


class WorkspaceUser(BaseModel):
    id: int
    username: str
    email: str
    plan: str
    scenario_count: int


class WorkspaceRoadmapSummary(BaseModel):
    id: int
    target_job: str
    updated_at: datetime
    # Normalized Fence plan; its shape is produced by plan normalization, not yet a schema.
    plan: dict[str, Any]


class WorkspaceStateResponse(BaseModel):
    user: WorkspaceUser
    profile: WorkspaceProfile
    preferences: WorkspacePreferences
    connections: dict[str, dict[str, Any]]
    saved_course_ids: list[str]
    roadmap: WorkspaceRoadmapSummary | None


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
    description: str | None = None
    annual_tuition: float | None = None
    currency: str | None = None
    duration_years: float | None = None
    study_mode: str | None = None
    program_name: str | None = None
    # "directory": name, country and website from the open university directory; nothing else is known yet.
    data_quality: Literal["database", "directory", "illustrative"]


class UniversityProfileLink(BaseModel):
    title: str
    url: str


class UniversityProfileOfficialPage(UniversityProfileLink):
    kind: Literal["admissions", "scholarships", "fees", "sport", "faculties", "international", "news"]


class UniversityProfileMention(BaseModel):
    """A sentence or list item copied from an official page, never rewritten."""
    text: str
    source_url: str


class UniversityProfileTuitionMention(UniversityProfileMention):
    """Amount parsed deterministically from an official fees page; verify before relying on it."""
    amount: ApiDecimal
    currency: str
    period: Literal["year", "semester", "month", "unknown"]


class UniversityProfileNewsItem(BaseModel):
    title: str
    url: str
    published_at: datetime | None = None
    source: str | None = None


class UniversityProfileImage(BaseModel):
    title: str
    url: str
    thumb_url: str
    source_url: str


class UniversityProfileFacts(BaseModel):
    founded: str | None = None
    students: int | None = None
    staff: int | None = None
    city: str | None = None
    logo_url: str | None = None
    image_url: str | None = None


class UniversityProfileResponse(BaseModel):
    status: Literal["ready", "partial", "unavailable"]
    fetched_at: datetime | None = None
    summary: str | None = None
    summary_source_url: str | None = None
    wikidata_url: str | None = None
    facts: UniversityProfileFacts = Field(default_factory=UniversityProfileFacts)
    faculties: list[str] = Field(default_factory=list)
    official_pages: list[UniversityProfileOfficialPage] = Field(default_factory=list)
    admission_documents: list[UniversityProfileMention] = Field(default_factory=list)
    scholarship_mentions: list[UniversityProfileMention] = Field(default_factory=list)
    tuition_mentions: list[UniversityProfileTuitionMention] = Field(default_factory=list)
    sport_mentions: list[UniversityProfileMention] = Field(default_factory=list)
    news: list[UniversityProfileNewsItem] = Field(default_factory=list)
    videos: list[UniversityProfileNewsItem] = Field(default_factory=list)
    gallery: list[UniversityProfileImage] = Field(default_factory=list)
    sources: list[UniversityProfileLink] = Field(default_factory=list)
    unavailable_sources: list[str] = Field(default_factory=list)


class WorkspaceUniversityDetailsResponse(WorkspaceUniversityResponse):
    programmes: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    scholarships: list[dict[str, Any]] = Field(default_factory=list)
    profile: UniversityProfileResponse | None = None


class EconomicPoint(BaseModel):
    period: date
    value: ApiDecimal


class EconomicSeries(BaseModel):
    indicator: str
    unit: str
    source_name: str
    source_url: str
    acquired_at: datetime
    points: list[EconomicPoint]


class CountryEconomicsResponse(BaseModel):
    """Official macro data and the deterministic defaults derived from it."""
    country: str
    currency: str | None
    latest_inflation_percent: ApiDecimal | None
    latest_inflation_year: int | None
    # Median of the last five annual CPI values: the suggested default for projections.
    suggested_inflation_percent: ApiDecimal | None
    inflation_window: str | None
    # Average yearly change of the local currency against EUR over the last five years; positive = devaluation.
    devaluation_vs_eur_percent: ApiDecimal | None
    baseline_monthly_wage: ApiDecimal | None = None
    baseline_wage_kind: Literal["minimum_wage", "median_vacancy_wage"] | None = None
    baseline_wage_period: date | None = None
    baseline_wage_source_name: str | None = None
    baseline_wage_source_url: str | None = None
    series: list[EconomicSeries]


class MarketNewsItem(BaseModel):
    title: str
    url: str
    published_at: datetime | None = None
    source: str | None = None


class MarketNewsResponse(BaseModel):
    query: str
    feed_url: str
    items: list[MarketNewsItem]


class RoadmapPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_job: str = Field(min_length=2, max_length=255)
    current_level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    hours_per_week: int = Field(default=8, ge=1, le=80)
    skills: list[str] = Field(default_factory=list, max_length=100)


class RoadmapTaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool


PaymentPlanId = Literal["pro", "business", "enterprise"]
BillingCycle = Literal["monthly", "yearly"]


class CheckoutRequest(BaseModel):
    # Unknown fields such as a client-sent amount are ignored: prices come from server config only.
    model_config = ConfigDict(extra="ignore")

    plan: PaymentPlanId
    cycle: BillingCycle


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PaymentPlanOption(BaseModel):
    plan: PaymentPlanId
    plan_name: str
    cycle: BillingCycle
    amount: int
    currency: str
    available: bool


class PaymentPlansResponse(BaseModel):
    configured: bool
    publishable_key: str | None
    current_plan: str | None
    options: list[PaymentPlanOption]


class PaymentStatusResponse(BaseModel):
    session_id: str
    plan: PaymentPlanId
    plan_name: str
    billing_cycle: BillingCycle
    status: Literal["pending", "paid", "failed", "expired", "canceled"]
    amount_expected: int
    amount_total: int | None
    currency: str
    paid_at: datetime | None
    created_at: datetime
    current_plan: str


class TrialProjectionRequest(BaseModel):
    """Anonymous trial calculation: the full engine on stored PL/UA data, nothing is saved."""
    model_config = ConfigDict(extra="forbid")

    country: Literal["Poland", "Ukraine"]
    career_target: str = Field(min_length=2, max_length=255)
    university: str | None = Field(default=None, max_length=255)
    study_years: ApiDecimal = Field(default=Decimal("4"), ge=Decimal("1"), le=Decimal("8"), decimal_places=1)
    annual_tuition: ApiDecimal = Field(default=Decimal("0"), ge=Decimal("0"), le=Decimal("1000000"), decimal_places=2)
    job_search_months: int = Field(default=3, ge=0, le=24)
    target_payback_years: int | None = Field(default=None, ge=1, le=30)


class TrialProjectionScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: Literal["pessimistic", "base", "optimistic"]
    start_salary: ApiDecimal
    roi_percent: ApiDecimal | None
    payback_months: int | None


class TrialProjectionYear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: int
    target_salary: ApiDecimal
    baseline_salary: ApiDecimal
    cumulative_incremental_earnings: ApiDecimal


class TrialProjectionSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    source_name: str
    source_reference: str | None = None
    sample_size: int | None = None
    confidence: str | None = None


class TrialProjectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview: Literal["trial"] = "trial"
    methodology_version: str
    country: str
    career_target: str
    university: str | None
    currency: str
    study_years: ApiDecimal
    annual_tuition: ApiDecimal
    total_direct_cost: ApiDecimal
    opportunity_cost: ApiDecimal
    total_investment: ApiDecimal
    estimated_start_salary: ApiDecimal
    baseline_annual_salary: ApiDecimal
    inflation_percent: ApiDecimal | None
    job_search_months: int
    horizon_years: int
    roi_percent: ApiDecimal | None
    payback_months: int | None
    payback_from_enrollment_months: int | None
    target_payback_years: int | None
    payback_within_target: bool | None
    payback_target_gap_months: int | None
    scenarios: list[TrialProjectionScenario]
    trajectory: list[TrialProjectionYear]
    sources: list[TrialProjectionSource]


class TrialProjectionOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str
    currency: str
    career_target: str
    median_salary: ApiDecimal
    seniority: str = "junior"
    # "listings": job adverts or salary survey; "official": Eurostat earnings survey estimate.
    salary_source: Literal["listings", "official"] = "listings"
