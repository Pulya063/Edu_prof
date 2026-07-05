from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

T = TypeVar("T")


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

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


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
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
    university: str = Field(min_length=2, max_length=255)
    degree_program: str = Field(min_length=2, max_length=255)
    country: str = Field(default="United States", min_length=2, max_length=120)
    tuition_cost: Decimal | None = Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2)
    study_duration_years: int = Field(default=4, ge=1, le=12)
    expected_start_salary: Decimal | None = Field(default=None, gt=Decimal("0"), max_digits=14, decimal_places=2)
    program_id: int | None = Field(default=None, gt=0)


class ROICalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roi_percent: Decimal
    break_even_months: int
    projected_income_5y: Decimal
    projected_income_10y: Decimal
    total_education_investment: Decimal
    career_growth_projection: list[Decimal]


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
    token: str
    new_password: str = Field(min_length=8, max_length=128)

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
