"""Add Gamification tables

Revision ID: 0003_add_gamification
Revises: 0002_add_test_runs
"""

from __future__ import annotations
import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_gamification"
down_revision = "0002_add_test_runs"
branch_labels = None
depends_on = None

_NOW = "NOW()"


def upgrade() -> None:
    op.create_table(
        "user_progress",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("xp", sa.Integer, nullable=False, server_default="0"),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("last_updated", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )
    
    op.create_table(
        "achievements",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("condition", sa.String, nullable=False),
    )
    
    op.create_table(
        "user_achievements",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("achievement_id", sa.UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.text(_NOW)),
    )


def downgrade() -> None:
    op.drop_table("user_achievements")
    op.drop_table("achievements")
    op.drop_table("user_progress")
