"""Добавить связи занятий снимка с преподавателями и аудиториями.

Revision ID: 20261127_03
Revises: 20261127_02
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20261127_03"
down_revision: str | None = "20261127_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создать таблицы связей с ID источника."""
    for table, related_id in (
        ("snapshot_entry_teacher", "teacher_id"),
        ("snapshot_entry_room", "room_id"),
        ("snapshot_entry_study_group", "study_group_id"),
        ("snapshot_entry_discipline", "discipline_id"),
    ):
        op.create_table(
            table,
            sa.Column("snapshot_id", sa.Uuid(), primary_key=True),
            sa.Column("entry_id", sa.String(64), primary_key=True),
            sa.Column(related_id, sa.String(64), primary_key=True),
            sa.ForeignKeyConstraint(
                ["snapshot_id", "entry_id"],
                ["snapshot_schedule_entry.snapshot_id", "snapshot_schedule_entry.source_id"],
                ondelete="CASCADE",
            ),
        )


def downgrade() -> None:
    """Удалить таблицы связей."""
    op.drop_table("snapshot_entry_discipline")
    op.drop_table("snapshot_entry_study_group")
    op.drop_table("snapshot_entry_room")
    op.drop_table("snapshot_entry_teacher")
