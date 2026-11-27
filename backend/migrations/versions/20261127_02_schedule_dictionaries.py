"""Создать локальные справочники расписания.

Revision ID: 20261127_02
Revises: 20261127_01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261127_02"
down_revision: str | None = "20261127_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создать таблицы групп, аудиторий, преподавателей и дисциплин."""
    op.create_table(
        "schedule_group",
        sa.Column("source_id", sa.String(64), primary_key=True),
        sa.Column("title", sa.Text()),
        sa.Column("short_title", sa.Text()),
        sa.Column("archived", sa.Boolean()),
    )
    op.create_table(
        "schedule_room",
        sa.Column("source_id", sa.String(64), primary_key=True),
        sa.Column("number", sa.Text()),
        sa.Column("title", sa.Text()),
        sa.Column("building_source_id", sa.String(64)),
    )
    op.create_table(
        "schedule_teacher",
        sa.Column("source_id", sa.String(64), primary_key=True),
        sa.Column("role_guid", sa.String(64)),
        sa.Column("last_name", sa.Text()),
        sa.Column("first_name", sa.Text()),
        sa.Column("middle_name", sa.Text()),
        sa.Column("removal_date", sa.DateTime(timezone=False)),
    )
    op.create_table(
        "schedule_discipline",
        sa.Column("source_id", sa.String(64), primary_key=True),
        sa.Column("title", sa.Text()),
        sa.Column("number", sa.Text()),
        sa.Column("user_code", sa.Text()),
        sa.Column("source_guid", sa.String(64)),
    )


def downgrade() -> None:
    """Удалить локальные справочники расписания."""
    op.drop_table("schedule_discipline")
    op.drop_table("schedule_teacher")
    op.drop_table("schedule_room")
    op.drop_table("schedule_group")
