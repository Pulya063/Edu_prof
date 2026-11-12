"""update

Revision ID: ec09cb2c7b62
Revises: 7f350ead4aec
Create Date: 2026-08-28 01:03:17.359820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec09cb2c7b62'
down_revision: Union[str, Sequence[str], None] = '7f350ead4aec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

