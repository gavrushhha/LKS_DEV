"""Создать основу локальных снимков расписания.

Revision ID: 20261127_01
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261127_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создать локальные таблицы снимков расписания."""
    op.create_table(
        "schedule_snapshot",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scope", sa.String(255), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('loading', 'ready', 'failed')", name="ck_schedule_snapshot_status"),
        sa.UniqueConstraint("scope", "id", name="uq_schedule_snapshot_scope_id"),
    )
    op.create_table(
        "snapshot_schedule_entry",
        sa.Column(
            "snapshot_id",
            sa.Uuid(),
            sa.ForeignKey("schedule_snapshot.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("source_id", sa.String(64), primary_key=True),
        sa.Column("lesson_date", sa.Date(), nullable=False),
        sa.Column("pair_number", sa.Integer(), nullable=True),
        sa.Column("start_minutes", sa.Integer(), nullable=True),
        sa.Column("end_minutes", sa.Integer(), nullable=True),
        sa.Column("activity", sa.String(255), nullable=True),
        sa.Column("place", sa.String(255), nullable=True),
        sa.Column("teachers", sa.String(255), nullable=True),
        sa.Column("groups", sa.String(255), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=False), nullable=True),
        sa.CheckConstraint(
            "start_minutes IS NULL OR start_minutes BETWEEN 0 AND 1439", name="ck_entry_start"
        ),
        sa.CheckConstraint("end_minutes IS NULL OR end_minutes BETWEEN 0 AND 1439", name="ck_entry_end"),
    )
    op.create_index(
        "ix_snapshot_entry_date", "snapshot_schedule_entry", ["snapshot_id", "lesson_date", "source_id"]
    )
    op.create_table(
        "active_schedule_snapshot",
        sa.Column("scope", sa.String(255), primary_key=True),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["scope", "snapshot_id"],
            ["schedule_snapshot.scope", "schedule_snapshot.id"],
            name="fk_active_snapshot_scope",
            ondelete="RESTRICT",
        ),
    )


def downgrade() -> None:
    """Удалить таблицы снимков и их индекс из БД ЛКС."""
    op.drop_table("active_schedule_snapshot")
    op.drop_index("ix_snapshot_entry_date", table_name="snapshot_schedule_entry")
    op.drop_table("snapshot_schedule_entry")
    op.drop_table("schedule_snapshot")
