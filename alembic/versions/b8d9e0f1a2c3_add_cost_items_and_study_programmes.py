"""Cost lines on projections and the study programme catalogue. Additive.

Revision ID: b8d9e0f1a2c3
Revises: a7c8d9e0f1b2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8d9e0f1a2c3"
down_revision: str | None = "a7c8d9e0f1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projection_inputs", sa.Column("cost_items", sa.JSON(), nullable=False, server_default="[]"))
    op.create_table(
        "study_programmes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("level", sa.String(60), nullable=True),
        sa.Column("study_mode", sa.String(60), nullable=True),
        sa.Column("annual_fee", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("university_id", "name", "level", "study_mode", name="uq_study_programme"),
    )
    op.create_index("ix_study_programmes_university_id", "study_programmes", ["university_id"])
    op.create_index("ix_study_programmes_country_name", "study_programmes", ["country", "name"])


def downgrade() -> None:
    op.drop_table("study_programmes")
    op.drop_column("projection_inputs", "cost_items")
