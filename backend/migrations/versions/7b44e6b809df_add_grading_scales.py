"""Создать таблицу шкал оценивания и добавить тестовые данные."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7b44e6b809df"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS education")
    op.create_table(
        "grading_scale",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("values", postgresql.ARRAY(sa.Text()), nullable=False, quote=True),
        sa.Column("pass_value", sa.Text(), nullable=True),
        sa.Column("brs_thresholds", postgresql.JSONB(), nullable=True),
        schema="education",
    )

    op.execute("""
        INSERT INTO education.grading_scale
            (id, name, "values", pass_value, brs_thresholds)
        VALUES
            (
                '22989c54-a40d-4cab-8b29-0e7b753d65b1',
                'Пятибалльная (тестовая)',
                ARRAY['2', '3', '4', '5'],
                '3',
                '[
                    {"min_points": 0, "grade": "2"},
                    {"min_points": 60.5, "grade": "3"},
                    {"min_points": 74, "grade": "4"},
                    {"min_points": 89.5, "grade": "5"}
                ]'::jsonb
            ),
            (
                '394b0e56-bbde-4d83-b42c-5795cfc8469d',
                'Зачётная (тестовая)',
                ARRAY['Не зачтено', 'Зачтено'],
                'Зачтено',
                NULL
            )
    """)


def downgrade() -> None:
    op.drop_table("grading_scale", schema="education")