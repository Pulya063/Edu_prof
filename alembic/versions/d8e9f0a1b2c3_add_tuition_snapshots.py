"""Add normalized tuition snapshots.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d8e9f0a1b2c3"
down_revision: str | None = "c7d8e9f0a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tuition_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(30), nullable=False),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("university", sa.String(255), nullable=True),
        sa.Column("program", sa.String(500), nullable=True),
        sa.Column("degree", sa.String(255), nullable=True),
        sa.Column("study_mode", sa.String(80), nullable=True),
        sa.Column(
            "student_residency",
            sa.String(40),
            server_default="unspecified",
            nullable=False,
        ),
        sa.Column("institution_type", sa.String(40), nullable=True),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("annual_tuition_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("annual_tuition", sa.Numeric(14, 2), nullable=False),
        sa.Column("annual_tuition_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("mandatory_fees", sa.Numeric(14, 2), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("methodology_version", sa.String(50), nullable=False),
        sa.Column(
            "validation_status",
            sa.String(20),
            server_default="validated",
            nullable=False,
        ),
        sa.Column("fingerprint", sa.String(64), nullable=False),
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
        sa.UniqueConstraint("fingerprint", name="uq_tuition_snapshot_fingerprint"),
    )
    op.create_index(
        "ix_tuition_snapshots_lookup",
        "tuition_snapshots",
        ["country", "university", "program", "degree", "currency", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_tuition_snapshots_lookup", table_name="tuition_snapshots")
    op.drop_table("tuition_snapshots")
