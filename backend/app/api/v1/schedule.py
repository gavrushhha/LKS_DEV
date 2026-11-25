"""Расписание — только чтение из БД Тандема (ТЗ, раздел 5)."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.core.deps import User, require_roles
from app.schemas.schedule import ScheduleEntry, ScheduleList, SourceStatus
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/schedule", tags=["Schedule"])

PERIOD_LIMIT_DAYS = 92


@router.get("", response_model=ScheduleList, summary="Расписание за период")
async def get_schedule(
    date_from: Annotated[date, Query()],
    date_to: Annotated[date, Query()],
    user: Annotated[
        User, Depends(require_roles("student", "teacher", "methodist", "curator", "admin", "parent"))
    ],
    group_id: str | None = None,
    teacher_id: str | None = None,
    room_id: str | None = None,
    student_id: str | None = None,
    lesson_type: str | None = None,
    include_cancelled: bool = False,
    view: Literal["flat", "by_day"] = "flat",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> ScheduleList:
    """TODO(T4.1): валидация фильтров, кэш Redis, выборка из source/tandem."""
    _ = (group_id, teacher_id, room_id, student_id, lesson_type, include_cancelled, view, limit, cursor)
    return await ScheduleService().get_schedule(user=user, date_from=date_from, date_to=date_to)


@router.get("/entries/{entry_id}", response_model=ScheduleEntry, summary="Карточка занятия")
async def get_schedule_entry(entry_id: str) -> ScheduleEntry:
    """TODO(T4.2)."""
    raise NotImplementedError(entry_id)


@router.get("/rooms/{room_id}/occupancy", summary="Занятость аудитории за день")
async def get_room_occupancy(room_id: str, date_: Annotated[date, Query(alias="date")]) -> dict[str, object]:
    """TODO(T4.3)."""
    raise NotImplementedError((room_id, date_))


@router.get("/bell-schedules", summary="Звонковое расписание")
async def list_bell_schedules() -> list[dict[str, object]]:
    """TODO(T4.4)."""
    raise NotImplementedError


@router.get("/source-status", response_model=SourceStatus, summary="Состояние источника расписания")
async def get_source_status(response: Response) -> SourceStatus:
    """Диагностика источника: режим, лаг, признак устаревания (ТЗ, 5.5)."""
    status = SourceStatus.from_settings()
    response.headers["Cache-Control"] = "no-store"
    return status
