"""Add soft-delete support for ROI calculations."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9b0c1d2e3f4"
down_revision: Union[str, Sequence[str], None] = "f8a9b0c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("roi_calculations", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_roi_calculations_deleted_at", "roi_calculations", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_roi_calculations_deleted_at", table_name="roi_calculations")
    op.drop_column("roi_calculations", "deleted_at")
