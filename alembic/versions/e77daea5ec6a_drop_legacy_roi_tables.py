"""drop_legacy_roi_tables

Revision ID: e77daea5ec6a
Revises: d8e9f0a1b2c3
Create Date: 2026-10-08 00:24:12.814281

"""
import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e77daea5ec6a'
down_revision: Union[str, Sequence[str], None] = 'd8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove superseded ROI writers and pre-snapshot salary tables.

    Child tables are removed before their parents so PostgreSQL can enforce
    foreign keys without relying on CASCADE.
    """
    # Preserve still-useful country averages in the normalized source table
    # before removing the legacy storage shape.
    bind = op.get_bind()
    legacy_tuition = bind.execute(sa.text(
        "SELECT country, academic_year, tuition_in_state, tuition_out_of_state, "
        "currency, source, source_url, created_at FROM tuition_prices"
    )).mappings()
    for row in legacy_tuition:
        values = [
            Decimal(str(value))
            for value in (row["tuition_in_state"], row["tuition_out_of_state"])
            if value is not None
        ]
        if not values:
            continue
        canonical = json.dumps(
            {
                "scope": "country_average",
                "country": row["country"],
                "academic_year": str(row["academic_year"]),
                "currency": row["currency"],
                "min": str(min(values)),
                "max": str(max(values)),
                "source": row["source"],
            },
            sort_keys=True,
        )
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        exists = bind.execute(
            sa.text("SELECT 1 FROM tuition_snapshots WHERE fingerprint=:fingerprint"),
            {"fingerprint": fingerprint},
        ).first()
        if exists:
            continue
        sources = [{"name": row["source"], "url": row["source_url"]}]
        bind.execute(sa.text(
            "INSERT INTO tuition_snapshots "
            "(scope,country,academic_year,snapshot_date,currency,annual_tuition_min,"
            "annual_tuition,annual_tuition_max,sources,acquired_at,confidence,"
            "methodology_version,validation_status,fingerprint) VALUES "
            "('country_average',:country,:academic_year,:snapshot_date,:currency,:minimum,"
            ":average,:maximum,:sources,:acquired_at,'medium','legacy-tuition-v1',"
            "'validated',:fingerprint)"
        ).bindparams(sa.bindparam("sources", type_=sa.JSON())), {
            "country": row["country"],
            "academic_year": str(row["academic_year"]),
            "snapshot_date": date(int(row["academic_year"]), 1, 1),
            "currency": row["currency"],
            "minimum": min(values),
            "average": sum(values) / len(values),
            "maximum": max(values),
            "sources": sources,
            "acquired_at": row["created_at"] or datetime.now(timezone.utc),
            "fingerprint": fingerprint,
        })

    for table_name in (
        'career_salary_bands',
        'career_scores',
        'career_education',
        'career_roi',
        'career_insights',
        'career_salary_forecasts',
        'roi_calculations',
        'career_analyses',
        'salary_statistics',
        'career_forecasts',
        'tuition_prices',
    ):
        op.drop_table(table_name)


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'tuition_prices',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('country', sa.String(120), nullable=False),
        sa.Column('academic_year', sa.Integer(), nullable=False),
        sa.Column('tuition_in_state', sa.Numeric(14, 2), nullable=True),
        sa.Column('tuition_out_of_state', sa.Numeric(14, 2), nullable=True),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('country', 'academic_year', name='uq_tuition_country_year'),
    )
    op.create_index('ix_tuition_prices_country', 'tuition_prices', ['country'])
    op.create_index('ix_tuition_prices_academic_year', 'tuition_prices', ['academic_year'])
    op.create_table('career_analyses',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('university', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('degree', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('specialization', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
    sa.Column('country', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('currency', sa.VARCHAR(length=3), server_default=sa.text("'USD'::character varying"), autoincrement=False, nullable=False),
    sa.Column('study_years', sa.NUMERIC(precision=4, scale=1), autoincrement=False, nullable=False),
    sa.Column('living_costs_included', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('career_analyses_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_analyses_pkey'))
    )
    op.create_index(op.f('ix_career_analyses_user_id'), 'career_analyses', ['user_id'], unique=False)
    op.create_index(op.f('ix_career_analyses_id'), 'career_analyses', ['id'], unique=False)
    op.create_table('roi_calculations',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('program_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_cost', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.Column('roi_percent', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('break_even_months', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('methodology_version', sa.VARCHAR(length=30), server_default=sa.text("'v1'::character varying"), autoincrement=False, nullable=False),
    sa.Column('deleted_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('study_years', sa.NUMERIC(precision=4, scale=1), server_default=sa.text("'4'::numeric"), autoincrement=False, nullable=False),
    sa.Column('possible_monthly_salary', sa.NUMERIC(precision=14, scale=2), server_default=sa.text("'0'::numeric"), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['education_programs.id'], name=op.f('roi_calculations_program_id_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('roi_calculations_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('roi_calculations_pkey'))
    )
    op.create_index(op.f('ix_roi_calculations_user_id'), 'roi_calculations', ['user_id'], unique=False)
    op.create_index(op.f('ix_roi_calculations_user_deleted_created'), 'roi_calculations', ['user_id', 'deleted_at', 'created_at'], unique=False)
    op.create_index(op.f('ix_roi_calculations_program_id'), 'roi_calculations', ['program_id'], unique=False)
    op.create_index(op.f('ix_roi_calculations_program_deleted'), 'roi_calculations', ['program_id', 'deleted_at'], unique=False)
    op.create_index(op.f('ix_roi_calculations_id'), 'roi_calculations', ['id'], unique=False)
    op.create_index(op.f('ix_roi_calculations_deleted_at'), 'roi_calculations', ['deleted_at'], unique=False)
    op.create_table('career_insights',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('analysis_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('kind', sa.VARCHAR(length=40), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=80), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['career_analyses.id'], name=op.f('career_insights_analysis_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_insights_pkey'))
    )
    op.create_index(op.f('ix_career_insights_id'), 'career_insights', ['id'], unique=False)
    op.create_index(op.f('ix_career_insights_analysis_kind'), 'career_insights', ['analysis_id', 'kind'], unique=False)
    op.create_index(op.f('ix_career_insights_analysis_id'), 'career_insights', ['analysis_id'], unique=False)
    op.create_table('career_roi',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('analysis_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('payback_likely', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('probability_percent', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('payback_months_min', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('payback_months_max', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('first_year_roi_min', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('first_year_roi_max', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False),
    sa.Column('long_term_roi', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['career_analyses.id'], name=op.f('career_roi_analysis_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_roi_pkey')),
    sa.UniqueConstraint('analysis_id', name=op.f('career_roi_analysis_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_career_roi_id'), 'career_roi', ['id'], unique=False)
    op.create_table('career_education',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('analysis_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('tuition_min', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.Column('tuition_max', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.Column('learning_budget_min', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.Column('learning_budget_max', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.Column('investment_min', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.Column('investment_max', sa.NUMERIC(precision=14, scale=2), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['career_analyses.id'], name=op.f('career_education_analysis_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_education_pkey')),
    sa.UniqueConstraint('analysis_id', name=op.f('career_education_analysis_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_career_education_id'), 'career_education', ['id'], unique=False)
    op.create_table('career_scores',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('analysis_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('career_potential', sa.NUMERIC(precision=5, scale=2), autoincrement=False, nullable=False),
    sa.Column('data_confidence', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['career_analyses.id'], name=op.f('career_scores_analysis_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_scores_pkey')),
    sa.UniqueConstraint('analysis_id', name=op.f('career_scores_analysis_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_career_scores_id'), 'career_scores', ['id'], unique=False)
    op.create_table('career_salary_forecasts',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('analysis_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('currency', sa.VARCHAR(length=3), server_default=sa.text("'USD'::character varying"), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['analysis_id'], ['career_analyses.id'], name=op.f('career_salary_forecasts_analysis_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_salary_forecasts_pkey')),
    sa.UniqueConstraint('analysis_id', name=op.f('career_salary_forecasts_analysis_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_career_salary_forecasts_id'), 'career_salary_forecasts', ['id'], unique=False)
    op.create_table('career_salary_bands',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('forecast_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('stage', sa.VARCHAR(length=40), autoincrement=False, nullable=False),
    sa.Column('monthly_min', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('monthly_max', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('realistic_target_min', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('realistic_target_max', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['forecast_id'], ['career_salary_forecasts.id'], name=op.f('career_salary_bands_forecast_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('career_salary_bands_pkey'))
    )
    op.create_index(op.f('ix_career_salary_bands_id'), 'career_salary_bands', ['id'], unique=False)
    op.create_index(op.f('ix_career_salary_bands_forecast_id'), 'career_salary_bands', ['forecast_id'], unique=False)
    op.create_table(
        'salary_statistics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profession', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=120), nullable=False),
        sa.Column('average_salary', sa.Numeric(14, 2), nullable=False),
        sa.Column('growth_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_salary_statistics_profession_country', 'salary_statistics', ['profession', 'country'])
    op.create_table(
        'career_forecasts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profession', sa.String(length=255), nullable=False),
        sa.Column('demand_score', sa.Integer(), nullable=False),
        sa.Column('ai_risk_score', sa.Integer(), nullable=False),
        sa.Column('forecast_growth_percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('forecast_year', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_career_forecasts_profession_year', 'career_forecasts', ['profession', 'forecast_year'])
