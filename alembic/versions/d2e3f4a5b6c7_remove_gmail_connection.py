"""Remove Gmail connection storage; Gmail API integration is deferred."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "5c53a63ad1b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_gmail_connections_disconnected_at", table_name="gmail_connections")
    op.drop_index("ix_gmail_connections_gmail_address", table_name="gmail_connections")
    op.drop_table("gmail_connections")


def downgrade() -> None:
    op.create_table(
        "gmail_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gmail_address", sa.String(320), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_gmail_connections_user"),
    )
    op.create_index("ix_gmail_connections_gmail_address", "gmail_connections", ["gmail_address"])
    op.create_index("ix_gmail_connections_disconnected_at", "gmail_connections", ["disconnected_at"])
