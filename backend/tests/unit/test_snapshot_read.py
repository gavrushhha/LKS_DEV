from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.schedule_snapshot import ActiveScheduleSnapshot, ScheduleSnapshot, SnapshotScheduleEntry
from app.services.snapshot_read import read_schedule_snapshot


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    for table in (
        ScheduleSnapshot.__table__,
        SnapshotScheduleEntry.__table__,
        ActiveScheduleSnapshot.__table__,
    ):
        table.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class SessionAdapter:
    def __init__(self, session):
        self.session = session

    async def execute(self, statement):
        return self.session.execute(statement)


async def read(db):
    return await read_schedule_snapshot(SessionAdapter(db), "group", 1, date(2026, 12, 7), date(2026, 12, 7))


async def test_missing_and_empty_ready_snapshot_are_distinct(db):
    assert await read(db) is None
    snapshot_id = uuid4()
    scope = "group:1:2026-12-07:2026-12-07"
    db.add(
        ScheduleSnapshot(
            id=snapshot_id,
            scope=scope,
            status="ready",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
    )
    db.add(ActiveScheduleSnapshot(scope=scope, snapshot_id=snapshot_id))
    db.commit()
    result = await read(db)
    assert result is not None and result.entries == () and result.snapshot_id == str(snapshot_id)


async def test_only_ready_active_snapshot_is_returned(db):
    snapshot_id = uuid4()
    scope = "group:1:2026-12-07:2026-12-07"
    snapshot = ScheduleSnapshot(id=snapshot_id, scope=scope, status="loading", started_at=datetime.now(UTC))
    db.add(snapshot)
    db.add(ActiveScheduleSnapshot(scope=scope, snapshot_id=snapshot_id))
    db.add(SnapshotScheduleEntry(snapshot_id=snapshot_id, source_id="123", lesson_date=date(2026, 12, 7)))
    db.commit()
    assert await read(db) is None
    snapshot.status = "ready"
    snapshot.completed_at = datetime.now(UTC)
    db.commit()
    result = await read(db)
    assert result is not None and [entry.source_id for entry in result.entries] == ["123"]
