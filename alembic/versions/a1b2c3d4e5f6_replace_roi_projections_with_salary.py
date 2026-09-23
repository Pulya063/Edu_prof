"""Replace long-horizon ROI projections with study duration and salary output."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("roi_calculations", sa.Column("study_years", sa.Numeric(precision=4, scale=1), nullable=False, server_default="4"))
    op.add_column(
        "roi_calculations",
        sa.Column("possible_monthly_salary", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
    )
    op.drop_column("roi_calculations", "projected_income_5y")
    op.drop_column("roi_calculations", "projected_income_10y")
    op.drop_column("roi_calculations", "npv_10y")


def downgrade() -> None:
    op.add_column("roi_calculations", sa.Column("projected_income_5y", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"))
    op.add_column("roi_calculations", sa.Column("projected_income_10y", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"))
    op.add_column("roi_calculations", sa.Column("npv_10y", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"))
    op.drop_column("roi_calculations", "possible_monthly_salary")
    op.drop_column("roi_calculations", "study_years")
