"""Тесты модуля schedule_snapshot."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.schedule_snapshot import ActiveScheduleSnapshot, ScheduleSnapshot, SnapshotScheduleEntry


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    ScheduleSnapshot.__table__.create(engine)
    SnapshotScheduleEntry.__table__.create(engine)
    ActiveScheduleSnapshot.__table__.create(engine)
    with Session(engine) as db:
        yield db
    engine.dispose()


def test_distinct_snapshots_can_contain_same_source_entry(session):
    first, second = uuid4(), uuid4()
    for snapshot_id in (first, second):
        session.add(
            ScheduleSnapshot(id=snapshot_id, scope="group:1", status="ready", started_at=datetime.now(UTC))
        )
    session.flush()
    for snapshot_id in (first, second):
        session.add(
            SnapshotScheduleEntry(snapshot_id=snapshot_id, source_id="42", lesson_date=date(2026, 12, 7))
        )
    session.commit()
    assert len(session.query(SnapshotScheduleEntry).all()) == 2


def test_active_snapshot_cannot_reference_other_scope(session):
    snapshot_id = uuid4()
    session.add(
        ScheduleSnapshot(id=snapshot_id, scope="group:1", status="ready", started_at=datetime.now(UTC))
    )
    session.flush()
    session.add(ActiveScheduleSnapshot(scope="group:2", snapshot_id=snapshot_id))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_minutes_outside_day_are_rejected(session):
    snapshot_id = uuid4()
    session.add(
        ScheduleSnapshot(id=snapshot_id, scope="group:1", status="loading", started_at=datetime.now(UTC))
    )
    session.flush()
    session.add(
        SnapshotScheduleEntry(
            snapshot_id=snapshot_id, source_id="42", lesson_date=date(2026, 12, 7), start_minutes=1440
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
