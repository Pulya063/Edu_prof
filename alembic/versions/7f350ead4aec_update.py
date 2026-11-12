"""update

Revision ID: 7f350ead4aec
Revises: a436d19786d1
Create Date: 2026-08-28 00:51:12.538063

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f350ead4aec'
down_revision: Union[str, Sequence[str], None] = 'a436d19786d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

