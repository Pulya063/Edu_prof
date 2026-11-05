"""Add economic indicators, university directory fields/profiles and v4 projection inputs.

Revision ID: c3e4f5a6b7d8
Revises: b2d3e4f5a6c7
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c3e4f5a6b7d8"
down_revision: str | None = "b2d3e4f5a6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "economic_indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("indicator", sa.String(40), nullable=False),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("country", "indicator", "period", "unit", name="uq_economic_indicator_point"),
    )
    op.create_index("ix_economic_indicators_id", "economic_indicators", ["id"])
    op.create_index("ix_economic_indicators_country", "economic_indicators", ["country"])

    op.add_column("universities", sa.Column("source", sa.String(60), nullable=True))
    op.add_column("universities", sa.Column("domains", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("universities", sa.Column("state_province", sa.String(120), nullable=True))

    op.create_table(
        "university_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "university_id",
            sa.Integer(),
            sa.ForeignKey("universities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payload", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_university_profiles_id", "university_profiles", ["id"])
    op.create_index("ix_university_profiles_university_id", "university_profiles", ["university_id"], unique=True)

    op.add_column("projection_inputs", sa.Column("inflation_percent", sa.Numeric(7, 3), nullable=True))
    op.add_column(
        "projection_inputs",
        sa.Column("job_search_months", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "projection_inputs",
        sa.Column("employment_probability_percent", sa.Numeric(7, 3), server_default="100", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("projection_inputs", "employment_probability_percent")
    op.drop_column("projection_inputs", "job_search_months")
    op.drop_column("projection_inputs", "inflation_percent")
    op.drop_index("ix_university_profiles_university_id", table_name="university_profiles")
    op.drop_index("ix_university_profiles_id", table_name="university_profiles")
    op.drop_table("university_profiles")
    op.drop_column("universities", "state_province")
    op.drop_column("universities", "domains")
    op.drop_column("universities", "source")
    op.drop_index("ix_economic_indicators_country", table_name="economic_indicators")
    op.drop_index("ix_economic_indicators_id", table_name="economic_indicators")
    op.drop_table("economic_indicators")
