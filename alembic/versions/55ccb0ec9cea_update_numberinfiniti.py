"""update_numberinfiniti

Revision ID: 55ccb0ec9cea
Revises: a5c68a91bc0f
Create Date: 2026-08-28 04:25:36.075532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55ccb0ec9cea'
down_revision: Union[str, Sequence[str], None] = 'a5c68a91bc0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

