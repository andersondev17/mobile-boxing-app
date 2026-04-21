"""Initial schema — v0001

Tables created:
- users (auth, profile)
- user_metrics (biomechanical aggregates)
- session_analytics (per-session summary)
- engagement_stats (usage tracking)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


# revision identifiers
revision: str = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

_NOW = "NOW()"


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=False, server_default=""),
        sa.Column("hashed_password", sa.String, nullable=True),
        sa.Column("provider", sa.String, nullable=False, server_default="email"),
        sa.Column("provider_id", sa.String, nullable=True),
        sa.Column("role", sa.String, nullable=False, server_default="user"),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("birth_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("height", sa.Float, nullable=True),   # cm
        sa.Column("weight", sa.Float, nullable=True),   # kg
        sa.Column("sex", sa.String(8), nullable=True),  # "M" | "F" | "Other"
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── user_metrics ──────────────────────────────────────────
    op.create_table(
        "user_metrics",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("avg_speed", sa.Float, nullable=False, server_default="0"),
        sa.Column("fatigue_index", sa.Float, nullable=False, server_default="0"),
        sa.Column("improvement_rate", sa.Float, nullable=False, server_default="0"),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )

    # ── session_analytics ─────────────────────────────────────
    op.create_table(
        "session_analytics",
        sa.Column("session_id", sa.String, primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("punch_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_sec", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("drop_off_point", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )
    op.create_index("ix_session_analytics_user_id", "session_analytics", ["user_id"])

    # ── engagement_stats ──────────────────────────────────────
    op.create_table(
        "engagement_stats",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("feature_usage", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("sessions_per_week", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_active", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )


def downgrade() -> None:
    op.drop_table("engagement_stats")
    op.drop_index("ix_session_analytics_user_id", table_name="session_analytics")
    op.drop_table("session_analytics")
    op.drop_table("user_metrics")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
