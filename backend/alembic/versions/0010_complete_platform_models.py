"""complete_platform_models

Revision ID: 0010_complete_platform_models
Revises: 0009_add_storage_backend
Create Date: 2026-09-27 12:00:00.000000

Adds all remaining platform models introduced across Phases 10 through 25:
- Multi-project domain catalogs & project definitions
- ML datasets, models, training runs, and predictions
- Optimization objectives, runs, candidates, and predictions
- Recommendations and parameter proposals
- ML validation, readiness checks, and drift monitoring
- Experimental validation framework & closed-loop candidate promotion
- Evidence records, quality gates, and provenance links
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.database.base import Base
import app.models  # noqa: F401 - Register all ORM models on Base.metadata

# revision identifiers, used by Alembic.
revision: str = "0010_complete_platform_models"
down_revision: Union[str, None] = "0009_add_storage_backend"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PHASE10_PLUS_TABLES = [
    # Project configuration & catalogs
    "material_catalogs",
    "biomass_catalogs",
    "extract_catalogs",
    "solvent_catalogs",
    "synthesis_method_catalogs",
    "project_definitions",
    # Optimization & Candidate generation
    "optimization_objectives",
    "optimization_runs",
    "candidates",
    "candidate_property_predictions",
    # Machine Learning Core
    "ml_datasets",
    "ml_dataset_records",
    "ml_models",
    "ml_training_runs",
    "ml_predictions",
    # ML Validation & Drift Monitoring
    "ml_readiness_checks",
    "model_reviews",
    "condition_deviations",
    "model_health_snapshots",
    "model_monitoring_events",
    "prediction_validations",
    "experiment_prediction_links",
    # Prospective Validation & Closed Loop
    "validation_criteria",
    "holdout_validations",
    "prospective_experiments",
    "validation_results",
    "dataset_candidates",
    "model_performance_snapshots",
    "recommendation_outcomes",
    "parameter_deviations",
    # Recommendation System
    "recommendations",
    "recommendation_parameters",
    # Evidence Layer
    "evidence_records",
    "evidence_links",
    "evidence_quality_gates",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name in PHASE10_PLUS_TABLES:
        if table_name in Base.metadata.tables and table_name not in existing_tables:
            Base.metadata.tables[table_name].create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    for table_name in reversed(PHASE10_PLUS_TABLES):
        if table_name in existing_tables:
            op.drop_table(table_name)
