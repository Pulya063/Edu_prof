"""message

Revision ID: 952a7ae698e7
Revises: f497d7a630cb
Create Date: 2026-08-27 23:38:27.333670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '952a7ae698e7'
down_revision: Union[str, Sequence[str], None] = 'f497d7a630cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

