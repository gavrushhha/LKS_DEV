"""Проверки применения миграций расписания к временной базе."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher
from app.models.schedule_snapshot import (
    ActiveScheduleSnapshot,
    ScheduleSnapshot,
    SnapshotEntryDiscipline,
    SnapshotEntryRoom,
    SnapshotEntryStudyGroup,
    SnapshotEntryTeacher,
    SnapshotScheduleEntry,
)

VERSIONS = Path(__file__).resolve().parents[2] / "migrations" / "versions"
MODELS = (
    ScheduleSnapshot,
    SnapshotScheduleEntry,
    ActiveScheduleSnapshot,
    ScheduleGroup,
    ScheduleRoom,
    ScheduleTeacher,
    ScheduleDiscipline,
    SnapshotEntryTeacher,
    SnapshotEntryRoom,
    SnapshotEntryStudyGroup,
    SnapshotEntryDiscipline,
)


def load_revision(filename):
    """Загрузить модуль миграции для применения к отдельной временной базе."""
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), VERSIONS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migrations_create_expected_columns_and_are_reversible():
    first = load_revision("20261127_01_schedule_snapshot.py")
    second = load_revision("20261127_02_schedule_dictionaries.py")
    third = load_revision("20261127_03_schedule_entry_links.py")
    assert second.down_revision == first.revision
    assert third.down_revision == second.revision
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            first.upgrade()
            second.upgrade()
            third.upgrade()
        inspector = inspect(connection)
        assert set(inspector.get_table_names()) == {model.__tablename__ for model in MODELS}
        for model in MODELS:
            columns = {column["name"] for column in inspector.get_columns(model.__tablename__)}
            assert columns == set(model.__table__.columns.keys())
            pk = set(inspector.get_pk_constraint(model.__tablename__)["constrained_columns"])
            assert pk == {column.name for column in model.__table__.primary_key.columns}
        with Operations.context(context):
            third.downgrade()
            second.downgrade()
            first.downgrade()
        assert inspect(connection).get_table_names() == []
    engine.dispose()
