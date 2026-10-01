"""update

Revision ID: a5c68a91bc0f
Revises: ec09cb2c7b62
Create Date: 2026-08-28 02:20:52.977598

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5c68a91bc0f'
down_revision: Union[str, Sequence[str], None] = 'ec09cb2c7b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass

