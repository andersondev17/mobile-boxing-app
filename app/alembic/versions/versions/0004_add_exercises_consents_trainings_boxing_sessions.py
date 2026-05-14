"""Add exercises, consents, trainings, and boxing_sessions tables.

Revision ID: 0004_add_exercises_consents_trainings_boxing_sessions
Revises: 0003_add_gamification
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_exercises_consents_trainings_boxing_sessions"
down_revision = "0003_add_gamification"
branch_labels = None
depends_on = None

_NOW = "NOW()"


def upgrade() -> None:
    # ── exercises ─────────────────────────────────────────────
    op.create_table(
        "exercises",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("poster_url", sa.String, nullable=True),
        sa.Column("video_url", sa.String, nullable=True),
        sa.Column("category", sa.String, nullable=True),
        sa.Column("difficulty", sa.String, nullable=True),
        sa.Column("duration_min", sa.Integer, nullable=False, server_default="5"),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("technique", sa.String, nullable=True),
        sa.Column("muscles", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("equipment", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )
    op.create_index("ix_exercises_title", "exercises", ["title"])
    op.create_index("ix_exercises_category", "exercises", ["category"])
    op.create_index("ix_exercises_difficulty", "exercises", ["difficulty"])

    # ── consents ────────────────────────────────────────────────
    op.create_table(
        "consents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("consent_type", sa.String, nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String, nullable=True),
        sa.Column("policy_version", sa.String, nullable=False, server_default="1.0"),
    )
    op.create_index("ix_consents_user_id", "consents", ["user_id"])
    op.create_index("ix_consents_consent_type", "consents", ["consent_type"])

    # ── trainings ─────────────────────────────────────────────
    op.create_table(
        "trainings",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("status", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_trainings_user_id", "trainings", ["user_id"])

    # ── boxing_sessions ─────────────────────────────────────
    op.create_table(
        "boxing_sessions",
        sa.Column("session_id", sa.String, primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("processed_filename", sa.String, nullable=False, server_default=""),
        sa.Column("frames_analyzed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("baseline_used", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("feedback_summary", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("metrics_path", sa.String, nullable=True),
        sa.Column("session_file", sa.String, nullable=True),
        sa.Column("session_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
        sa.Column("punch_type_detected", sa.String, nullable=True),
        sa.Column("punch_type_confirmed", sa.String, nullable=True),
        sa.Column("user_corrected", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_boxing_sessions_user_id", "boxing_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_boxing_sessions_user_id", table_name="boxing_sessions")
    op.drop_table("boxing_sessions")

    op.drop_index("ix_trainings_user_id", table_name="trainings")
    op.drop_table("trainings")

    op.drop_index("ix_consents_consent_type", table_name="consents")
    op.drop_index("ix_consents_user_id", table_name="consents")
    op.drop_table("consents")

    op.drop_index("ix_exercises_difficulty", table_name="exercises")
    op.drop_index("ix_exercises_category", table_name="exercises")
    op.drop_index("ix_exercises_title", table_name="exercises")
    op.drop_table("exercises")
