"""Persist normalized full career analyses, including anonymous trials."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "career_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("university", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(255), nullable=False),
        sa.Column("specialization", sa.String(500), nullable=False),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("study_years", sa.Numeric(4, 1), nullable=False),
        sa.Column("living_costs_included", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_career_analyses_user_id", "career_analyses", ["user_id"])

    op.create_table(
        "career_education",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("career_analyses.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("tuition_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("tuition_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("learning_budget_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("learning_budget_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("investment_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("investment_max", sa.Numeric(14, 2), nullable=False),
    )
    op.create_table(
        "career_salary_forecasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("career_analyses.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
    )
    op.create_table(
        "career_salary_bands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("forecast_id", sa.Integer(), sa.ForeignKey("career_salary_forecasts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("monthly_min", sa.Integer(), nullable=False),
        sa.Column("monthly_max", sa.Integer(), nullable=False),
        sa.Column("realistic_target_min", sa.Integer(), nullable=True),
        sa.Column("realistic_target_max", sa.Integer(), nullable=True),
    )
    op.create_index("ix_career_salary_bands_forecast_id", "career_salary_bands", ["forecast_id"])
    op.create_table(
        "career_roi",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("career_analyses.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("payback_likely", sa.Boolean(), nullable=False),
        sa.Column("probability_percent", sa.Integer(), nullable=False),
        sa.Column("payback_months_min", sa.Integer(), nullable=False),
        sa.Column("payback_months_max", sa.Integer(), nullable=False),
        sa.Column("first_year_roi_min", sa.Numeric(10, 2), nullable=False),
        sa.Column("first_year_roi_max", sa.Numeric(10, 2), nullable=False),
        sa.Column("long_term_roi", sa.String(20), nullable=False),
    )
    op.create_table(
        "career_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("career_analyses.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("career_potential", sa.Numeric(5, 2), nullable=False),
        sa.Column("data_confidence", sa.Integer(), nullable=False),
    )
    op.create_table(
        "career_insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("career_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
    )
    op.create_index("ix_career_insights_analysis_id", "career_insights", ["analysis_id"])


def downgrade() -> None:
    op.drop_index("ix_career_insights_analysis_id", table_name="career_insights")
    op.drop_table("career_insights")
    op.drop_table("career_scores")
    op.drop_table("career_roi")
    op.drop_index("ix_career_salary_bands_forecast_id", table_name="career_salary_bands")
    op.drop_table("career_salary_bands")
    op.drop_table("career_salary_forecasts")
    op.drop_table("career_education")
    op.drop_index("ix_career_analyses_user_id", table_name="career_analyses")
    op.drop_table("career_analyses")
