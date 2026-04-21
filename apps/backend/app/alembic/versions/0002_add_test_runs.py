"""Add test_runs table — web testing persistence.

Revision ID: 0002_add_test_runs
Revises: 0001_initial_schema
"""

from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_test_runs"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

_NOW = "NOW()"


def upgrade() -> None:
    op.create_table(
        "test_runs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("video_name", sa.String, nullable=False),
        sa.Column("total_frames", sa.Integer, nullable=False, server_default="0"),
        sa.Column("scored_frames", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("min_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("max_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("punch_type", sa.String, nullable=True),
        sa.Column("feedback", sa.Text, nullable=True),   # JSON array as text
        sa.Column("processing_ms", sa.Float, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )
    op.create_index("ix_test_runs_user_id", "test_runs", ["user_id"])
    op.create_index("ix_test_runs_created_at", "test_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_test_runs_created_at", table_name="test_runs")
    op.drop_index("ix_test_runs_user_id", table_name="test_runs")
    op.drop_table("test_runs")
