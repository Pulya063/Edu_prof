"""Normalize projection details and add advisory AI reviews.

Revision ID: f0a1b2c3d4e5
Revises: e77daea5ec6a
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f0a1b2c3d4e5"
down_revision: str | None = "e77daea5ec6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _decimal(value: object | None) -> Decimal:
    return Decimal(str(value or 0))


def _datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _json_value(value: object, fallback: object) -> object:
    """Normalize JSON values returned as text by some migration dialects."""
    if value is None:
        return fallback
    if isinstance(value, str):
        return json.loads(value)
    return value


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def upgrade() -> None:
    op.create_table(
        "projection_inputs",
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("annual_start_salary", sa.Numeric(18, 2), nullable=False),
        sa.Column("baseline_annual_salary", sa.Numeric(18, 2), nullable=False),
        sa.Column("annual_salary_growth_percent", sa.Numeric(7, 3), nullable=False),
        sa.Column("baseline_salary_growth_percent", sa.Numeric(7, 3), nullable=False),
        sa.Column("foregone_income_percent", sa.Numeric(7, 3), nullable=False),
        sa.Column("mandatory_fees", sa.Numeric(18, 2), nullable=False),
        sa.Column("scholarships_and_grants", sa.Numeric(18, 2), nullable=False),
        sa.Column("additional_education_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("incremental_living_cost", sa.Numeric(18, 2), nullable=False),
        sa.Column("employment_income_during_study", sa.Numeric(18, 2), nullable=True),
        sa.Column("horizon_years", sa.Integer(), nullable=False),
        sa.Column("market_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("salary_source_kind", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["market_snapshot_id"], ["market_snapshots.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("projection_id"),
    )
    op.create_table(
        "projection_costs",
        sa.Column("projection_id", sa.Integer(), nullable=False),
        *[
            sa.Column(name, sa.Numeric(18, 2), nullable=False)
            for name in (
                "tuition", "mandatory_fees", "additional_education", "incremental_living_cost",
                "scholarships_and_grants", "gross_direct_cost", "net_direct_cost",
                "baseline_income_during_study", "employment_income_during_study", "opportunity_cost",
            )
        ],
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("projection_id"),
    )
    op.create_table(
        "projection_trajectory_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("target_salary", sa.Numeric(18, 2), nullable=False),
        sa.Column("baseline_salary", sa.Numeric(18, 2), nullable=False),
        sa.Column("incremental_earnings", sa.Numeric(18, 2), nullable=False),
        sa.Column("cumulative_incremental_earnings", sa.Numeric(20, 2), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("projection_id", "year", name="uq_projection_trajectory_year"),
    )
    op.create_index("ix_projection_trajectory_points_projection_id", "projection_trajectory_points", ["projection_id"])
    op.create_table(
        "projection_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_reference", sa.String(1000), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country", sa.String(120), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column("seniority", sa.String(120), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_projection_evidence_projection_metric", "projection_evidence", ["projection_id", "metric"])
    op.create_table(
        "projection_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(30), nullable=False),
        sa.Column("reference", sa.String(255), nullable=False),
        sa.Column("market_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("tuition_snapshot_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["market_snapshot_id"], ["market_snapshots.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tuition_snapshot_id"], ["tuition_snapshots.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_projection_sources_projection_id", "projection_sources", ["projection_id"])
    op.create_table(
        "projection_warnings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("projection_id", "code", name="uq_projection_warning_code"),
    )
    op.create_index("ix_projection_warnings_projection_id", "projection_warnings", ["projection_id"])
    op.create_table(
        "projection_ai_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), server_default="pending", nullable=False),
        sa.Column("provider_model", sa.String(255), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("ai_risk_score", sa.Integer(), nullable=True),
        sa.Column("calculation_consistent", sa.Boolean(), nullable=True),
        sa.Column("prediction_summary", sa.Text(), nullable=True),
        sa.Column("verdict", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("risks", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("suggested_adjustments", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["simulation_projections.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("projection_id", name="uq_projection_ai_review_projection"),
    )
    op.create_index("ix_projection_ai_reviews_projection_id", "projection_ai_reviews", ["projection_id"])

    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id, calculation_inputs, cost_breakdown, salary_trajectory, evidence, "
        "source_snapshot_refs, unverified_assumptions FROM simulation_projections"
    )).mappings()
    for row in rows:
        projection_id = row["id"]
        inputs = _json_value(row["calculation_inputs"], {})
        refs = _json_value(row["source_snapshot_refs"], [])
        market_id = next((int(ref) for ref in refs if str(ref).isdigit()), None)
        bind.execute(sa.text(
            "INSERT INTO projection_inputs "
            "(projection_id,annual_start_salary,baseline_annual_salary,annual_salary_growth_percent,"
            "baseline_salary_growth_percent,foregone_income_percent,mandatory_fees,"
            "scholarships_and_grants,additional_education_cost,incremental_living_cost,"
            "employment_income_during_study,horizon_years,market_snapshot_id,salary_source_kind) VALUES "
            "(:projection_id,:annual_start_salary,:baseline_annual_salary,:annual_salary_growth_percent,"
            ":baseline_salary_growth_percent,:foregone_income_percent,:mandatory_fees,"
            ":scholarships_and_grants,:additional_education_cost,:incremental_living_cost,"
            ":employment_income_during_study,:horizon_years,:market_snapshot_id,:salary_source_kind)"
        ), {
            "projection_id": projection_id,
            "annual_start_salary": _decimal(inputs.get("annual_start_salary")),
            "baseline_annual_salary": _decimal(inputs.get("baseline_annual_salary")),
            "annual_salary_growth_percent": _decimal(inputs.get("annual_salary_growth_percent")),
            "baseline_salary_growth_percent": _decimal(inputs.get("baseline_salary_growth_percent")),
            "foregone_income_percent": _decimal(inputs.get("foregone_income_percent", 100)),
            "mandatory_fees": _decimal(inputs.get("mandatory_fees")),
            "scholarships_and_grants": _decimal(inputs.get("scholarships_and_grants")),
            "additional_education_cost": _decimal(inputs.get("additional_education_cost")),
            "incremental_living_cost": _decimal(inputs.get("incremental_living_cost")),
            "employment_income_during_study": inputs.get("employment_income_during_study"),
            "horizon_years": int(inputs.get("horizon_years", 10)),
            "market_snapshot_id": market_id,
            "salary_source_kind": "market_snapshot" if market_id else "manual_evidence",
        })
        costs = _json_value(row["cost_breakdown"], {})
        bind.execute(sa.text(
            "INSERT INTO projection_costs "
            "(projection_id,tuition,mandatory_fees,additional_education,incremental_living_cost,"
            "scholarships_and_grants,gross_direct_cost,net_direct_cost,baseline_income_during_study,"
            "employment_income_during_study,opportunity_cost) VALUES "
            "(:projection_id,:tuition,:mandatory_fees,:additional_education,:incremental_living_cost,"
            ":scholarships_and_grants,:gross_direct_cost,:net_direct_cost,:baseline_income_during_study,"
            ":employment_income_during_study,:opportunity_cost)"
        ), {"projection_id": projection_id, **{key: _decimal(costs.get(key)) for key in (
            "tuition", "mandatory_fees", "additional_education", "incremental_living_cost",
            "scholarships_and_grants", "gross_direct_cost", "net_direct_cost",
            "baseline_income_during_study", "employment_income_during_study", "opportunity_cost",
        )}})
        for point in _json_value(row["salary_trajectory"], []):
            bind.execute(sa.text(
                "INSERT INTO projection_trajectory_points "
                "(projection_id,year,target_salary,baseline_salary,incremental_earnings,cumulative_incremental_earnings) "
                "VALUES (:projection_id,:year,:target_salary,:baseline_salary,:incremental_earnings,:cumulative_incremental_earnings)"
            ), {"projection_id": projection_id, **point})
        for item in _json_value(row["evidence"], []):
            bind.execute(sa.text(
                "INSERT INTO projection_evidence "
                "(projection_id,metric,source_name,source_reference,acquired_at,country,role,seniority,currency,sample_size,confidence) "
                "VALUES (:projection_id,:metric,:source_name,:source_reference,:acquired_at,:country,:role,:seniority,:currency,:sample_size,:confidence)"
            ), {"projection_id": projection_id, **item, "acquired_at": _datetime(item["acquired_at"])})
            reference = str(item.get("source_reference", ""))
            if reference.startswith("tuition_snapshot:"):
                tuition_id = int(reference.split(":", 1)[1])
                bind.execute(sa.text(
                    "INSERT INTO projection_sources (projection_id,source_kind,reference,tuition_snapshot_id) "
                    "VALUES (:projection_id,'tuition_snapshot',:reference,:tuition_id)"
                ), {"projection_id": projection_id, "reference": reference, "tuition_id": tuition_id})
        for ref in refs:
            ref_text = str(ref)
            bind.execute(sa.text(
                "INSERT INTO projection_sources (projection_id,source_kind,reference,market_snapshot_id) "
                "VALUES (:projection_id,'market_snapshot',:reference,:market_id)"
            ), {"projection_id": projection_id, "reference": ref_text, "market_id": int(ref_text) if ref_text.isdigit() else None})
        for code in _json_value(row["unverified_assumptions"], []):
            bind.execute(sa.text(
                "INSERT INTO projection_warnings (projection_id,code) VALUES (:projection_id,:code)"
            ), {"projection_id": projection_id, "code": str(code)})

    for column in (
        "calculation_inputs", "cost_breakdown", "salary_trajectory", "evidence",
        "source_snapshot_refs", "unverified_assumptions",
    ):
        op.drop_column("simulation_projections", column)

    op.alter_column("simulation_projections", "total_direct_cost", type_=sa.Numeric(20, 2))
    op.alter_column("simulation_projections", "opportunity_cost", type_=sa.Numeric(20, 2))
    op.alter_column("simulation_projections", "total_investment", type_=sa.Numeric(20, 2))
    op.alter_column("simulation_projections", "estimated_start_salary", type_=sa.Numeric(18, 2))
    op.alter_column("simulation_projections", "cumulative_incremental_earnings", type_=sa.Numeric(20, 2))
    op.alter_column("simulation_projections", "roi_percent", type_=sa.Numeric(18, 2))


def downgrade() -> None:
    op.add_column("simulation_projections", sa.Column("calculation_inputs", sa.JSON(), nullable=True))
    op.add_column("simulation_projections", sa.Column("cost_breakdown", sa.JSON(), nullable=True))
    op.add_column("simulation_projections", sa.Column("salary_trajectory", sa.JSON(), nullable=True))
    op.add_column("simulation_projections", sa.Column("evidence", sa.JSON(), nullable=True))
    op.add_column("simulation_projections", sa.Column("source_snapshot_refs", sa.JSON(), nullable=True))
    op.add_column("simulation_projections", sa.Column("unverified_assumptions", sa.JSON(), nullable=True))

    bind = op.get_bind()
    projection_ids = bind.execute(sa.text("SELECT id FROM simulation_projections")).scalars()
    for projection_id in projection_ids:
        inputs = bind.execute(sa.text("SELECT * FROM projection_inputs WHERE projection_id=:id"), {"id": projection_id}).mappings().first()
        costs = bind.execute(sa.text("SELECT * FROM projection_costs WHERE projection_id=:id"), {"id": projection_id}).mappings().first()
        trajectory = [dict(row) for row in bind.execute(sa.text("SELECT year,target_salary,baseline_salary,incremental_earnings,cumulative_incremental_earnings FROM projection_trajectory_points WHERE projection_id=:id ORDER BY year"), {"id": projection_id}).mappings()]
        evidence = [dict(row) for row in bind.execute(sa.text("SELECT metric,source_name,source_reference,acquired_at,country,role,seniority,currency,sample_size,confidence FROM projection_evidence WHERE projection_id=:id ORDER BY id"), {"id": projection_id}).mappings()]
        refs = list(bind.execute(sa.text("SELECT reference FROM projection_sources WHERE projection_id=:id ORDER BY id"), {"id": projection_id}).scalars())
        warnings = list(bind.execute(sa.text("SELECT code FROM projection_warnings WHERE projection_id=:id ORDER BY id"), {"id": projection_id}).scalars())
        bind.execute(sa.text(
            "UPDATE simulation_projections SET calculation_inputs=:inputs,cost_breakdown=:costs,"
            "salary_trajectory=:trajectory,evidence=:evidence,source_snapshot_refs=:refs,"
            "unverified_assumptions=:warnings WHERE id=:id"
        ).bindparams(
            sa.bindparam("inputs", type_=sa.JSON()), sa.bindparam("costs", type_=sa.JSON()),
            sa.bindparam("trajectory", type_=sa.JSON()), sa.bindparam("evidence", type_=sa.JSON()),
            sa.bindparam("refs", type_=sa.JSON()), sa.bindparam("warnings", type_=sa.JSON()),
        ), {
            "id": projection_id,
            "inputs": _json_safe({key: value for key, value in dict(inputs or {}).items() if key not in {"projection_id", "salary_source_kind"}}),
            "costs": _json_safe({key: value for key, value in dict(costs or {}).items() if key != "projection_id"}),
            "trajectory": _json_safe(trajectory), "evidence": _json_safe(evidence),
            "refs": refs, "warnings": warnings,
        })

    for table_name in (
        "projection_ai_reviews", "projection_warnings", "projection_sources", "projection_evidence",
        "projection_trajectory_points", "projection_costs", "projection_inputs",
    ):
        op.drop_table(table_name)

    for column in (
        "calculation_inputs", "cost_breakdown", "salary_trajectory", "evidence",
        "source_snapshot_refs", "unverified_assumptions",
    ):
        op.alter_column("simulation_projections", column, nullable=False)
    op.alter_column("simulation_projections", "total_direct_cost", type_=sa.Numeric(14, 2))
    op.alter_column("simulation_projections", "opportunity_cost", type_=sa.Numeric(14, 2))
    op.alter_column("simulation_projections", "total_investment", type_=sa.Numeric(14, 2))
    op.alter_column("simulation_projections", "estimated_start_salary", type_=sa.Numeric(14, 2))
    op.alter_column("simulation_projections", "cumulative_incremental_earnings", type_=sa.Numeric(16, 2))
    op.alter_column("simulation_projections", "roi_percent", type_=sa.Numeric(10, 2))
