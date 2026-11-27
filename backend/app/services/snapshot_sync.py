"""Загрузка ограниченного снимка расписания в БД ЛКС."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.schedule_snapshot import ActiveScheduleSnapshot, ScheduleSnapshot, SnapshotScheduleEntry
from app.source.tandem.mapping import map_schedule_core
from app.source.tandem.schedule_reader import FilterKind, TandemScheduleReader

_LIMIT = 200


class IncompleteSnapshotError(ValueError):
    """Объём ответа не позволяет доказать полноту снимка."""


def _write_snapshot(session: Session, scope: str, entries: list[SnapshotScheduleEntry]) -> str:
    """Записать снимок и переключить указатель внутри транзакции вызывающего кода."""
    snapshot_id = uuid4()
    now = datetime.now(UTC)
    session.add(ScheduleSnapshot(id=snapshot_id, scope=scope, status="loading", started_at=now))
    session.flush()
    for entry in entries:
        entry.snapshot_id = snapshot_id
    session.add_all(entries)
    session.flush()
    snapshot = session.get(ScheduleSnapshot, snapshot_id)
    assert snapshot is not None
    snapshot.status = "ready"
    snapshot.completed_at = datetime.now(UTC)
    active = session.scalar(
        select(ActiveScheduleSnapshot).where(ActiveScheduleSnapshot.scope == scope).with_for_update()
    )
    if active is None:
        session.add(ActiveScheduleSnapshot(scope=scope, snapshot_id=snapshot_id))
    else:
        active.snapshot_id = snapshot_id
    session.flush()
    return str(snapshot_id)


def _entry(row: dict[str, Any], fetched_at: datetime) -> SnapshotScheduleEntry:
    """Проверить и перенести подтверждённые поля одной строки источника."""
    core = map_schedule_core(row, fetched_at)
    values = [row[name] for name in ("activity_p", "place_p", "pps_p", "students_p")]
    if any(value is not None and (not isinstance(value, str) or len(value) > 255) for value in values):
        raise ValueError("Текстовое поле занятия не помещается в локальную таблицу")
    if core.updated_at is not None and core.updated_at.utcoffset() is not None:
        raise ValueError("Время источника должно быть без часового пояса")
    return SnapshotScheduleEntry(
        source_id=core.id,
        lesson_date=core.date,
        pair_number=core.pair_number,
        start_minutes=row["starttime_p"],
        end_minutes=row["endtime_p"],
        activity=values[0],
        place=values[1],
        teachers=values[2],
        groups=values[3],
        source_updated_at=core.updated_at,
    )


async def sync_schedule_snapshot(
    reader: TandemScheduleReader,
    session: AsyncSession,
    kind: FilterKind,
    source_id: int,
    date_from: date,
    date_to: date,
) -> str:
    """Загрузить полную ограниченную выборку и атомарно заменить снимок данной области."""
    rows = await reader.fetch(kind, source_id, date_from, date_to, limit=_LIMIT)
    if len(rows) >= _LIMIT:
        raise IncompleteSnapshotError("Достигнут лимит источника: полнота снимка не подтверждена")
    fetched_at = datetime.now(UTC)
    entries = [_entry(row, fetched_at) for row in rows]
    if any(not date_from <= entry.lesson_date <= date_to for entry in entries):
        raise ValueError("Источник вернул занятие за пределами запрошенного периода")
    if len({entry.source_id for entry in entries}) != len(entries):
        raise ValueError("Источник вернул повторяющийся идентификатор занятия")
    scope = f"{kind}:{source_id}:{date_from.isoformat()}:{date_to.isoformat()}"
    async with session.begin():
        return await session.run_sync(_write_snapshot, scope, entries)
