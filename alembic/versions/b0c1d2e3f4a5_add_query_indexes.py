"""Add composite indexes for common filtering and joins."""

from typing import Sequence, Union

from alembic import op


revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_universities_country_name",
        "universities",
        ["country", "name"],
    )
    op.create_index(
        "ix_education_programs_university_name",
        "education_programs",
        ["university_id", "name"],
    )
    op.create_index(
        "ix_salary_statistics_profession_country",
        "salary_statistics",
        ["profession", "country"],
    )
    op.create_index(
        "ix_career_forecasts_profession_year",
        "career_forecasts",
        ["profession", "forecast_year"],
    )
    op.create_index(
        "ix_career_insights_analysis_kind",
        "career_insights",
        ["analysis_id", "kind"],
    )
    op.create_index(
        "ix_roi_calculations_user_deleted_created",
        "roi_calculations",
        ["user_id", "deleted_at", "created_at"],
    )
    op.create_index(
        "ix_roi_calculations_program_deleted",
        "roi_calculations",
        ["program_id", "deleted_at"],
    )
    op.create_index(
        "ix_user_roadmaps_user_updated",
        "user_roadmaps",
        ["user_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_roadmaps_user_updated", table_name="user_roadmaps")
    op.drop_index("ix_roi_calculations_program_deleted", table_name="roi_calculations")
    op.drop_index("ix_roi_calculations_user_deleted_created", table_name="roi_calculations")
    op.drop_index("ix_career_insights_analysis_kind", table_name="career_insights")
    op.drop_index("ix_career_forecasts_profession_year", table_name="career_forecasts")
    op.drop_index("ix_salary_statistics_profession_country", table_name="salary_statistics")
    op.drop_index("ix_education_programs_university_name", table_name="education_programs")
    op.drop_index("ix_universities_country_name", table_name="universities")
