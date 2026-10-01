"""update

Revision ID: 4e8e8067a603
Revises: addb8d7b23d1
Create Date: 2026-08-28 00:06:09.138325

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e8e8067a603'
down_revision: Union[str, Sequence[str], None] = 'addb8d7b23d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

