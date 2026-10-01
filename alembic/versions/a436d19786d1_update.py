"""update

Revision ID: a436d19786d1
Revises: 4e8e8067a603
Create Date: 2026-08-28 00:20:12.966258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a436d19786d1'
down_revision: Union[str, Sequence[str], None] = '4e8e8067a603'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

