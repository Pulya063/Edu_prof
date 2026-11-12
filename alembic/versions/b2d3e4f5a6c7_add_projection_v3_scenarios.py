"""Add scenario-projection-v3 fields: scenario outcomes, NPV and discount rate.

Revision ID: b2d3e4f5a6c7
Revises: a1c2e3f4b5d6
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b2d3e4f5a6c7"
down_revision: str | None = "a1c2e3f4b5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("simulation_projections", sa.Column("npv", sa.Numeric(20, 2), nullable=True))
    op.add_column(
        "simulation_projections",
        sa.Column("scenario_outcomes", sa.JSON(), server_default="[]", nullable=False),
    )
    op.add_column("projection_inputs", sa.Column("discount_rate_percent", sa.Numeric(7, 3), nullable=True))


def downgrade() -> None:
    op.drop_column("projection_inputs", "discount_rate_percent")
    op.drop_column("simulation_projections", "scenario_outcomes")
    op.drop_column("simulation_projections", "npv")
