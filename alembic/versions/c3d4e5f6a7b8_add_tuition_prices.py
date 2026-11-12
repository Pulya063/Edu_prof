"""Add normalized tuition reference data."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b9f1c3e2a7d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tuition_prices",
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("tuition_in_state", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("tuition_out_of_state", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("country", "academic_year", name="uq_tuition_country_year"),
    )
    op.create_index("ix_tuition_prices_id", "tuition_prices", ["id"], unique=False)
    op.create_index("ix_tuition_prices_country", "tuition_prices", ["country"], unique=False)
    op.create_index("ix_tuition_prices_academic_year", "tuition_prices", ["academic_year"], unique=False)

    tuition_table = sa.table(
        "tuition_prices",
        sa.column("country", sa.String),
        sa.column("academic_year", sa.Integer),
        sa.column("tuition_in_state", sa.Numeric),
        sa.column("tuition_out_of_state", sa.Numeric),
        sa.column("currency", sa.String),
        sa.column("source", sa.String),
    )
    op.bulk_insert(
        tuition_table,
        [
            {
                "country": "Ukraine",
                "academic_year": year,
                "tuition_in_state": in_state,
                "tuition_out_of_state": out_of_state,
                "currency": "USD",
                "source": "legacy_non_us_tuition_dataset",
            }
            for year, in_state, out_of_state in [
                (2018, 1200, 2500),
                (2019, 1350, 2700),
                (2020, 1400, 2800),
                (2021, 1500, 3000),
                (2022, 1600, 3200),
                (2023, 1700, 3400),
            ]
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_tuition_prices_academic_year", table_name="tuition_prices")
    op.drop_index("ix_tuition_prices_country", table_name="tuition_prices")
    op.drop_index("ix_tuition_prices_id", table_name="tuition_prices")
    op.drop_table("tuition_prices")
