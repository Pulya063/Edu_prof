"""Add the optional target payback period and its verdict (scenario-projection-v5).

Revision ID: a7c8d9e0f1b2
Revises: c3e4f5a6b7d8
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a7c8d9e0f1b2"
down_revision: str | None = "c3e4f5a6b7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projection_inputs", sa.Column("target_payback_years", sa.Integer(), nullable=True))
    op.add_column("simulation_projections", sa.Column("target_payback_years", sa.Integer(), nullable=True))
    op.add_column("simulation_projections", sa.Column("payback_within_target", sa.Boolean(), nullable=True))
    op.add_column("simulation_projections", sa.Column("payback_target_gap_months", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("simulation_projections", "payback_target_gap_months")
    op.drop_column("simulation_projections", "payback_within_target")
    op.drop_column("simulation_projections", "target_payback_years")
    op.drop_column("projection_inputs", "target_payback_years")
