"""Add deterministic simulation projections.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_projections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "revision_id",
            sa.Integer(),
            sa.ForeignKey("simulation_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("methodology_version", sa.String(50), nullable=False),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("salary_basis", sa.String(30), nullable=False),
        sa.Column("total_direct_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("opportunity_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_investment", sa.Numeric(14, 2), nullable=False),
        sa.Column("estimated_start_salary", sa.Numeric(14, 2), nullable=False),
        sa.Column("payback_months", sa.Integer(), nullable=True),
        sa.Column("break_even_reached", sa.Boolean(), nullable=False),
        sa.Column("horizon_years", sa.Integer(), nullable=False),
        sa.Column("cumulative_incremental_earnings", sa.Numeric(16, 2), nullable=False),
        sa.Column("roi_percent", sa.Numeric(10, 2), nullable=True),
        sa.Column("salary_trajectory", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("unverified_assumptions", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "revision_id",
            "methodology_version",
            "input_fingerprint",
            name="uq_simulation_projection_input",
        ),
    )
    op.create_index(
        "ix_simulation_projections_revision_created",
        "simulation_projections",
        ["revision_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_simulation_projections_revision_created",
        table_name="simulation_projections",
    )
    op.drop_table("simulation_projections")
