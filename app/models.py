from datetime import datetime
from decimal import Decimal
from typing import ClassVar

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.core.database import Base


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


class User(BaseIDMixin, TimestampMixin, ReprMixin, Base):
    __tablename__ = "users"
    repr_fields = ("id", "email")

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    roi_calculations: Mapped[list["ROICalculation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class University(BaseIDMixin, TimestampMixin, ReprMixin, Base):
    __tablename__ = "universities"
    repr_fields = ("id", "name")

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    programs: Mapped[list["EducationProgram"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EducationProgram(BaseIDMixin, TimestampMixin, ReprMixin, Base):
    __tablename__ = "education_programs"
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


class SalaryStatistic(BaseIDMixin, TimestampMixin, ReprMixin, Base):
    __tablename__ = "salary_statistics"
    repr_fields = ("id", "profession", "country")

    profession: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    country: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    average_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    growth_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)


class CareerForecast(BaseIDMixin, TimestampMixin, ReprMixin, Base):
    __tablename__ = "career_forecasts"
    repr_fields = ("id", "profession", "forecast_year")

    profession: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    demand_score: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_growth_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    forecast_year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)


class ROICalculation(BaseIDMixin, TimestampMixin, ReprMixin, Base):
    __tablename__ = "roi_calculations"
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
    projected_income_5y: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    projected_income_10y: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    user: Mapped[User] = relationship(back_populates="roi_calculations")
    program: Mapped[EducationProgram | None] = relationship(back_populates="roi_calculations")
