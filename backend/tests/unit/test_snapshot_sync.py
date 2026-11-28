"""Тесты модуля snapshot_sync."""

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.schedule_snapshot import (
    ActiveScheduleSnapshot,
    ScheduleSnapshot,
    SnapshotEntryDiscipline,
    SnapshotEntryRoom,
    SnapshotEntryStudyGroup,
    SnapshotEntryTeacher,
    SnapshotScheduleEntry,
)
from app.services.snapshot_sync import (
    IncompleteSnapshotError,
    _entry,
    _write_snapshot,
    sync_schedule_snapshot,
)
from app.source.tandem.schedule_reader import TandemScheduleReader


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    for table in (
        ScheduleSnapshot.__table__,
        SnapshotScheduleEntry.__table__,
        SnapshotEntryTeacher.__table__,
        SnapshotEntryRoom.__table__,
        SnapshotEntryStudyGroup.__table__,
        SnapshotEntryDiscipline.__table__,
        ActiveScheduleSnapshot.__table__,
    ):
        table.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def row():
    return {
        "id": 123,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": 1,
        "starttime_p": 525,
        "endtime_p": 605,
        "sysupdatedate_p": None,
        "activity_p": "Математика",
        "place_p": "101",
        "pps_p": "Преподаватель",
        "students_p": "Группа",
        "teacher_ids": [501],
        "room_ids": [601, 602],
        "study_group_ids": [701],
        "discipline_ids": [801],
    }


def test_publish_replaces_pointer_and_retains_previous_data(db):
    scope = "group:1:2026-12-07:2026-12-07"
    with db.begin():
        first = _write_snapshot(db, scope, [_entry(row(), datetime.now(UTC))])
    with db.begin():
        second = _write_snapshot(db, scope, [_entry(row(), datetime.now(UTC))])
    active = db.get(ActiveScheduleSnapshot, scope)
    assert str(active.snapshot_id) == second != first
    assert db.query(SnapshotScheduleEntry).count() == 2
    assert db.query(ScheduleSnapshot).filter_by(status="ready").count() == 2


def test_error_rolls_back_new_snapshot_and_preserves_active(db):
    scope = "group:1:2026-12-07:2026-12-07"
    with db.begin():
        first = _write_snapshot(db, scope, [_entry(row(), datetime.now(UTC))])
    with pytest.raises(IntegrityError), db.begin():
        _write_snapshot(db, scope, [_entry(row(), datetime.now(UTC)), _entry(row(), datetime.now(UTC))])
    assert str(db.get(ActiveScheduleSnapshot, scope).snapshot_id) == first
    assert db.query(ScheduleSnapshot).count() == 1


async def test_limit_never_publishes_incomplete_snapshot():
    reader = AsyncMock(spec=TandemScheduleReader)
    reader.fetch.return_value = [row()] * 200
    session = AsyncMock()
    with pytest.raises(IncompleteSnapshotError):
        await sync_schedule_snapshot(reader, session, "group", 1, date(2026, 12, 7), date(2026, 12, 7))
    session.begin.assert_not_called()


@pytest.mark.parametrize("invalid_rows", [[row(), row()], [{**row(), "date_p": date(2026, 12, 8)}]])
async def test_invalid_data_never_starts_publication(invalid_rows):
    reader = AsyncMock(spec=TandemScheduleReader)
    reader.fetch.return_value = invalid_rows
    session = AsyncMock()
    with pytest.raises(ValueError):
        await sync_schedule_snapshot(reader, session, "group", 1, date(2026, 12, 7), date(2026, 12, 7))
    session.begin.assert_not_called()


async def test_invalid_teacher_links_do_not_publish():
    reader, session = AsyncMock(), AsyncMock()
    reader.fetch.return_value = [{**row(), "teacher_ids": [1, 1]}]
    with pytest.raises(ValueError):
        await sync_schedule_snapshot(reader, session, "group", 1, date(2026, 12, 7), date(2026, 12, 7))
    session.begin.assert_not_called()


def test_null_text_fields_from_tandem_are_preserved():
    source = {**row(), "activity_p": None, "pps_p": None, "students_p": None}
    entry = _entry(source, datetime.now(UTC))
    assert (entry.activity, entry.teachers, entry.groups, entry.place) == (None, None, None, "101")


def test_event_without_bell_keeps_missing_pair():
    """Сохранить отсутствие номера пары у события без звонка."""
    source = {**row(), "bellentrynumber_p": None, "discipline_ids": []}
    assert _entry(source, datetime.now(UTC)).pair_number is None


async def test_sync_reads_source_and_publishes_in_one_transaction(db):
    class AsyncSessionAdapter:
        @asynccontextmanager
        async def begin(self):
            with db.begin():
                yield

        async def run_sync(self, function, *args):
            return function(db, *args)

    reader = AsyncMock(spec=TandemScheduleReader)
    reader.fetch.return_value = [row()]
    result = await sync_schedule_snapshot(
        reader, AsyncSessionAdapter(), "group", 1, date(2026, 12, 7), date(2026, 12, 7)
    )
    assert str(db.get(ActiveScheduleSnapshot, "group:1:2026-12-07:2026-12-07").snapshot_id) == result
    assert db.query(SnapshotEntryTeacher).one().teacher_id == "501"
    assert {room.room_id for room in db.query(SnapshotEntryRoom).all()} == {"601", "602"}
    assert db.query(SnapshotEntryStudyGroup).one().study_group_id == "701"
    assert db.query(SnapshotEntryDiscipline).one().discipline_id == "801"
    reader.fetch.assert_awaited_once_with("group", 1, date(2026, 12, 7), date(2026, 12, 7), limit=200)
