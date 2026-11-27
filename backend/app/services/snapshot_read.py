"""Чтение активного локального снимка для точно заданной области."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleRoom, ScheduleTeacher
from app.models.schedule_snapshot import (
    ActiveScheduleSnapshot,
    ScheduleSnapshot,
    SnapshotEntryDiscipline,
    SnapshotEntryRoom,
    SnapshotEntryStudyGroup,
    SnapshotEntryTeacher,
    SnapshotScheduleEntry,
)
from app.source.tandem.schedule_reader import FilterKind


@dataclass(frozen=True)
class SnapshotResult:
    """Время обновления и занятия одного готового снимка."""

    snapshot_id: str
    completed_at: datetime
    entries: tuple[SnapshotScheduleEntry, ...]


@dataclass(frozen=True)
class SnapshotEntryLink:
    """ID занятия и связанной записи источника."""

    entry_id: str
    kind: str
    source_id: str
    name: str | None


async def read_snapshot_links(session: AsyncSession, snapshot_id: UUID) -> tuple[SnapshotEntryLink, ...]:
    """Прочитать связи занятий одного снимка с преподавателями, аудиториями и учебными группами."""
    query = union_all(
        select(
            SnapshotEntryTeacher.entry_id,
            literal("teacher"),
            SnapshotEntryTeacher.teacher_id,
            func.nullif(
                func.trim(
                    func.coalesce(ScheduleTeacher.last_name, "")
                    + " "
                    + func.coalesce(ScheduleTeacher.first_name, "")
                    + " "
                    + func.coalesce(ScheduleTeacher.middle_name, "")
                ),
                "",
            ),
        )
        .outerjoin(ScheduleTeacher, ScheduleTeacher.source_id == SnapshotEntryTeacher.teacher_id)
        .where(SnapshotEntryTeacher.snapshot_id == snapshot_id),
        select(
            SnapshotEntryRoom.entry_id,
            literal("room"),
            SnapshotEntryRoom.room_id,
            func.coalesce(ScheduleRoom.title, ScheduleRoom.number),
        )
        .outerjoin(ScheduleRoom, ScheduleRoom.source_id == SnapshotEntryRoom.room_id)
        .where(SnapshotEntryRoom.snapshot_id == snapshot_id),
        select(
            SnapshotEntryStudyGroup.entry_id,
            literal("study_group"),
            SnapshotEntryStudyGroup.study_group_id,
            literal(None),
        ).where(SnapshotEntryStudyGroup.snapshot_id == snapshot_id),
        select(
            SnapshotEntryDiscipline.entry_id,
            literal("discipline"),
            SnapshotEntryDiscipline.discipline_id,
            ScheduleDiscipline.title,
        )
        .outerjoin(ScheduleDiscipline, ScheduleDiscipline.source_id == SnapshotEntryDiscipline.discipline_id)
        .where(SnapshotEntryDiscipline.snapshot_id == snapshot_id),
    )
    rows = (await session.execute(query)).all()
    return tuple(
        SnapshotEntryLink(entry_id=row[0], kind=row[1], source_id=row[2], name=row[3]) for row in rows
    )


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
