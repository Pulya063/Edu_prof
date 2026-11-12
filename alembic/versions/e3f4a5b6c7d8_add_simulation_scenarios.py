"""Add versioned simulation scenarios.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "simulation_scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), server_default="active", nullable=False),
        sa.Column("current_revision_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("target_role", sa.String(255), nullable=False),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_simulation_scenarios_user_updated", "simulation_scenarios", ["user_id", "updated_at"])

    op.create_table(
        "simulation_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("simulation_scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("methodology_version", sa.String(50), server_default="scenario-foundation-v1", nullable=False),
        sa.Column("source_snapshot_refs", sa.JSON(), nullable=False),
        sa.Column("change_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("scenario_id", "revision_number", name="uq_simulation_revision_number"),
    )
    op.create_index("ix_simulation_revisions_scenario_created", "simulation_revisions", ["scenario_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_simulation_revisions_scenario_created", table_name="simulation_revisions")
    op.drop_table("simulation_revisions")
    op.drop_index("ix_simulation_scenarios_user_updated", table_name="simulation_scenarios")
    op.drop_table("simulation_scenarios")
