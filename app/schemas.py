from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar

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


class UniversityCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    country: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=1, max_length=120)
    website: HttpUrl | None = None


class UniversityResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: str
    city: str
    website: str | None = None


class EducationProgramCreateSchema(BaseModel):
    university_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    duration_years: int = Field(ge=1, le=12)
    tuition_cost: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    expected_start_salary: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    annual_growth_percent: Decimal = Field(ge=Decimal("-50"), le=Decimal("100"), max_digits=5, decimal_places=2)


class EducationProgramResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    university_id: int
    name: str
    description: str | None
    duration_years: int
    tuition_cost: Decimal
    expected_start_salary: Decimal
    annual_growth_percent: Decimal


class ROICalculationRequest(BaseModel):
    """The only business inputs accepted by the ROI calculation API."""

    model_config = ConfigDict(extra="forbid")

    university: str = Field(min_length=2, max_length=255)
    faculty: str = Field(min_length=2, max_length=255)
    annual_tuition: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    study_years: Decimal = Field(default=Decimal("4"), ge=Decimal("1"), le=Decimal("12"), decimal_places=1)


class CareerAnalysisRequest(BaseModel):
    """Inputs for the full education and career decision analysis."""

    model_config = ConfigDict(extra="forbid")

    university: str = Field(min_length=2, max_length=255)
    degree: str = Field(min_length=2, max_length=255)
    specialization_focus: str = Field(min_length=2, max_length=500)
    country: str = Field(default="United States", min_length=2, max_length=120)
    currency: str = Field(default="USD", pattern="^USD$")
    study_years: Decimal = Field(ge=Decimal("1"), le=Decimal("12"), decimal_places=1)
    monthly_payment: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    payments_per_year: int = Field(default=12, ge=1, le=24)
    additional_learning_budget_min: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    additional_learning_budget_max: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), max_digits=14, decimal_places=2)
    include_living_costs: bool = False

    @model_validator(mode="after")
    def validate_budget_range(self) -> "CareerAnalysisRequest":
        if self.additional_learning_budget_max < self.additional_learning_budget_min:
            raise ValueError("Максимальний бюджет не може бути меншим за мінімальний")
        return self


class ROICalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    roi_percent: Decimal
    break_even_months: int
    total_education_investment: Decimal
    career_growth_projection: list[Decimal]
    study_years: Decimal
    possible_monthly_salary: Decimal
    methodology_version: str = "v2-scenario"
    created_at: datetime | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: T | None = None


class PaginationSchema(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total: int = Field(default=0, ge=0)


class SalaryStatisticSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    profession: str = Field(min_length=2, max_length=255)
    country: str = Field(min_length=2, max_length=120)
    average_salary: Decimal = Field(gt=Decimal("0"), max_digits=14, decimal_places=2)
    growth_rate: Decimal = Field(ge=Decimal("-50"), le=Decimal("100"), max_digits=5, decimal_places=2)


class CareerForecastSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    profession: str = Field(min_length=2, max_length=255)
    demand_score: int = Field(ge=0, le=100)
    ai_risk_score: int = Field(ge=0, le=100)
    forecast_growth_percent: Decimal = Field(ge=Decimal("-50"), le=Decimal("100"), max_digits=5, decimal_places=2)
    forecast_year: int = Field(ge=2024, le=2100)


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
