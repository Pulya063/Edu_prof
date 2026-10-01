"""Add validated market snapshots and projection references.

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "simulation_projections",
        sa.Column("source_snapshot_refs", sa.JSON(), server_default="[]", nullable=False),
    )
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("seniority", sa.String(120), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("salary_basis", sa.String(30), server_default="gross_annual", nullable=False),
        sa.Column("salary_min", sa.Numeric(14, 2), nullable=False),
        sa.Column("median_salary", sa.Numeric(14, 2), nullable=False),
        sa.Column("salary_max", sa.Numeric(14, 2), nullable=False),
        sa.Column("vacancy_count", sa.Integer(), nullable=True),
        sa.Column("demand_index", sa.Numeric(5, 2), nullable=True),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("methodology_version", sa.String(50), nullable=False),
        sa.Column("validation_status", sa.String(20), server_default="validated", nullable=False),
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
        sa.UniqueConstraint("fingerprint", name="uq_market_snapshot_fingerprint"),
    )
    op.create_index(
        "ix_market_snapshots_lookup",
        "market_snapshots",
        ["country", "role", "seniority", "currency", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_snapshots_lookup", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_column("simulation_projections", "source_snapshot_refs")
