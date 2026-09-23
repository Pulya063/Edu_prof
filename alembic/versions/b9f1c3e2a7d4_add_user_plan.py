"""Add plan to users."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b9f1c3e2a7d4"
down_revision: Union[str, Sequence[str], None] = "55ccb0ec9cea"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("plan", sa.String(length=20), nullable=False, server_default="Free"))


def downgrade() -> None:
    op.drop_column("users", "plan")
