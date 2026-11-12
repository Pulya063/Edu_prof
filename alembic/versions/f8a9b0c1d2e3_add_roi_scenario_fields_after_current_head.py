"""Preserve the superseded ROI scenario migration in the history.

The canonical scenario-field migration is ``d4e5f6a7b8c9``.  This revision
is retained as a no-op so existing revision references remain resolvable,
while the graph has one linear head and the columns are not added twice.
"""

from typing import Sequence, Union

revision: str = "f8a9b0c1d2e3"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
