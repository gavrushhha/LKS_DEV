"""Чтение активного локального снимка для точно заданной области."""

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schedule_snapshot import ActiveScheduleSnapshot, ScheduleSnapshot, SnapshotScheduleEntry
from app.source.tandem.schedule_reader import FilterKind


@dataclass(frozen=True)
class SnapshotResult:
    """Время обновления и занятия одного готового снимка."""

    snapshot_id: str
    completed_at: datetime
    entries: tuple[SnapshotScheduleEntry, ...]


async def read_schedule_snapshot(
    session: AsyncSession, kind: FilterKind, source_id: int, date_from: date, date_to: date
) -> SnapshotResult | None:
    """Прочитать готовый снимок по точной области; None означает отсутствие снимка."""
    if kind not in ("group", "teacher", "room", "student"):
        raise ValueError("Неизвестный фильтр расписания")
    if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id <= 0:
        raise ValueError("Идентификатор должен быть положительным целым числом")
    if date_to < date_from or (date_to - date_from).days >= settings.allowed_period_days:
        raise ValueError("Недопустимый период расписания")
    scope = f"{kind}:{source_id}:{date_from.isoformat()}:{date_to.isoformat()}"
    stmt = (
        select(ScheduleSnapshot, SnapshotScheduleEntry)
        .join(ActiveScheduleSnapshot, ActiveScheduleSnapshot.snapshot_id == ScheduleSnapshot.id)
        .outerjoin(SnapshotScheduleEntry, SnapshotScheduleEntry.snapshot_id == ScheduleSnapshot.id)
        .where(
            and_(
                ActiveScheduleSnapshot.scope == scope,
                ScheduleSnapshot.scope == scope,
                ScheduleSnapshot.status == "ready",
                ScheduleSnapshot.completed_at.is_not(None),
            )
        )
        .order_by(
            SnapshotScheduleEntry.lesson_date,
            SnapshotScheduleEntry.pair_number,
            SnapshotScheduleEntry.source_id,
        )
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return None
    snapshot = rows[0][0]
    assert snapshot.completed_at is not None
    return SnapshotResult(
        snapshot_id=str(snapshot.id),
        completed_at=snapshot.completed_at,
        entries=tuple(entry for _, entry in rows if entry is not None),
    )
