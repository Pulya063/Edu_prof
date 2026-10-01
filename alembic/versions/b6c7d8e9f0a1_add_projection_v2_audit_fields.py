"""Add reproducible inputs and cost breakdown to simulation projections.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "simulation_projections",
        sa.Column("calculation_inputs", sa.JSON(), server_default="{}", nullable=False),
    )
    op.add_column(
        "simulation_projections",
        sa.Column("cost_breakdown", sa.JSON(), server_default="{}", nullable=False),
    )
    op.add_column(
        "simulation_projections",
        sa.Column("payback_from_enrollment_months", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("simulation_projections", "payback_from_enrollment_months")
    op.drop_column("simulation_projections", "cost_breakdown")
    op.drop_column("simulation_projections", "calculation_inputs")
