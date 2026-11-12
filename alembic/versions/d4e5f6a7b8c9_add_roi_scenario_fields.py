"""Add scenario-aware ROI fields."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "eb1b392c8ea9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "roi_calculations",
        sa.Column("npv_10y", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "roi_calculations",
        sa.Column("methodology_version", sa.String(length=30), nullable=False, server_default="v1"),
    )


def downgrade() -> None:
    op.drop_column("roi_calculations", "methodology_version")
    op.drop_column("roi_calculations", "npv_10y")
