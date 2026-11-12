"""Add university communication, documents, scholarships and partners."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b0c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("partner_type", sa.String(60), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("contact_email", sa.String(320), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_partners_is_active_name", "partners", ["is_active", "name"])

    op.create_table(
        "university_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("subject_name", sa.String(255), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("university_id", "subject_name", "title", name="uq_university_documents_subject_title"),
    )
    op.create_index("ix_university_documents_university_id", "university_documents", ["university_id"])
    op.create_index("ix_university_documents_university_subject", "university_documents", ["university_id", "subject_name"])

    op.create_table(
        "university_scholarships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("eligibility", sa.Text(), nullable=True),
        sa.Column("application_url", sa.String(1000), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_university_scholarships_university_id", "university_scholarships", ["university_id"])
    op.create_index("ix_university_scholarships_university_deadline", "university_scholarships", ["university_id", "deadline"])

    op.create_table(
        "motivation_letters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("university_id", sa.Integer(), sa.ForeignKey("universities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("generation_prompt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("ai_model", sa.String(80), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_motivation_letters_user_id", "motivation_letters", ["user_id"])
    op.create_index("ix_motivation_letters_university_id", "motivation_letters", ["university_id"])
    op.create_index("ix_motivation_letters_user_status", "motivation_letters", ["user_id", "status"])

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

def downgrade() -> None:
    op.drop_index("ix_gmail_connections_disconnected_at", table_name="gmail_connections")
    op.drop_index("ix_gmail_connections_gmail_address", table_name="gmail_connections")
    op.drop_table("gmail_connections")

    for index_name in (
        "ix_motivation_letters_user_status",
        "ix_motivation_letters_university_id",
        "ix_motivation_letters_user_id",
    ):
        op.drop_index(index_name, table_name="motivation_letters")
    op.drop_table("motivation_letters")

    op.drop_index("ix_university_scholarships_university_deadline", table_name="university_scholarships")
    op.drop_index("ix_university_scholarships_university_id", table_name="university_scholarships")
    op.drop_table("university_scholarships")

    op.drop_index("ix_university_documents_university_subject", table_name="university_documents")
    op.drop_index("ix_university_documents_university_id", table_name="university_documents")
    op.drop_table("university_documents")

    op.drop_index("ix_partners_is_active_name", table_name="partners")
    op.drop_table("partners")
