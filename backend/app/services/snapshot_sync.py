"""Загрузка ограниченного снимка расписания в БД ЛКС."""

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.schedule_snapshot import (
    ActiveScheduleSnapshot,
    ScheduleSnapshot,
    SnapshotEntryDiscipline,
    SnapshotEntryRoom,
    SnapshotEntryStudyGroup,
    SnapshotEntryTeacher,
    SnapshotScheduleEntry,
)
from app.source.tandem.mapping import map_schedule_core, map_schedule_links
from app.source.tandem.schedule_reader import FilterKind, TandemScheduleReader

_LIMIT = 200
logger = get_logger(__name__)


class IncompleteSnapshotError(ValueError):
    """Объём ответа не позволяет доказать полноту снимка."""


def _write_snapshot(
    session: Session,
    scope: str,
    entries: list[SnapshotScheduleEntry],
    links: list[tuple[str, str, str]] | None = None,
) -> str:
    """Записать снимок и переключить указатель внутри транзакции вызывающего кода."""
    snapshot_id = uuid4()
    now = datetime.now(UTC)
    session.add(ScheduleSnapshot(id=snapshot_id, scope=scope, status="loading", started_at=now))
    session.flush()
    for entry in entries:
        entry.snapshot_id = snapshot_id
    session.add_all(entries)
    session.flush()
    for entry_id, kind, related_id in links or []:
        if kind == "teacher":
            session.add(
                SnapshotEntryTeacher(snapshot_id=snapshot_id, entry_id=entry_id, teacher_id=related_id)
            )
        elif kind == "room":
            session.add(SnapshotEntryRoom(snapshot_id=snapshot_id, entry_id=entry_id, room_id=related_id))
        elif kind == "study_group":
            session.add(
                SnapshotEntryStudyGroup(snapshot_id=snapshot_id, entry_id=entry_id, study_group_id=related_id)
            )
        elif kind == "discipline":
            session.add(
                SnapshotEntryDiscipline(snapshot_id=snapshot_id, entry_id=entry_id, discipline_id=related_id)
            )
        else:
            raise ValueError("Неизвестный тип связи занятия")
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
    logger.info("schedule_snapshot_started", filter_kind=kind)
    rows = await reader.fetch(kind, source_id, date_from, date_to, limit=_LIMIT)
    if len(rows) >= _LIMIT:
        raise IncompleteSnapshotError("Достигнут лимит источника: полнота снимка не подтверждена")
    fetched_at = datetime.now(UTC)
    entries = [_entry(row, fetched_at) for row in rows]
    if any(not date_from <= entry.lesson_date <= date_to for entry in entries):
        raise ValueError("Источник вернул занятие за пределами запрошенного периода")
    if len({entry.source_id for entry in entries}) != len(entries):
        raise ValueError("Источник вернул повторяющийся идентификатор занятия")
    links: list[tuple[str, str, str]] = []
    for entry, row in zip(entries, rows, strict=True):
        links.extend((entry.source_id, kind, related_id) for kind, related_id in map_schedule_links(row))
    scope = f"{kind}:{source_id}:{date_from.isoformat()}:{date_to.isoformat()}"
    async with session.begin():
        snapshot_id = await session.run_sync(_write_snapshot, scope, entries, links)
    logger.info("schedule_snapshot_synced", filter_kind=kind, entries_count=len(entries))
    return snapshot_id
