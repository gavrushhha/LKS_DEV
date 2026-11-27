"""Чтение локальных справочников расписания из БД ЛКС."""

from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher

DictionaryKind = Literal["group", "room", "teacher", "discipline"]
DictionaryRecord = ScheduleGroup | ScheduleRoom | ScheduleTeacher | ScheduleDiscipline


async def read_dictionary_item(
    session: AsyncSession, kind: DictionaryKind, source_id: str
) -> DictionaryRecord | None:
    """Найти запись локального справочника по строковому ID источника."""
    models: dict[str, type[DictionaryRecord]] = {
        "group": ScheduleGroup,
        "room": ScheduleRoom,
        "teacher": ScheduleTeacher,
        "discipline": ScheduleDiscipline,
    }
    if kind not in models:
        raise ValueError("Неизвестный справочник")
    if not isinstance(source_id, str) or not source_id or len(source_id) > 64:
        raise ValueError("Некорректный идентификатор")
    return cast(DictionaryRecord | None, await session.get(models[kind], source_id))


async def read_dictionary_page(
    session: AsyncSession,
    kind: DictionaryKind,
    *,
    after_id: str | None = None,
    limit: int = 100,
) -> tuple[list[DictionaryRecord], str | None]:
    """Прочитать страницу по строковому ID; курсор равен ID последней записи."""
    models: dict[str, type[DictionaryRecord]] = {
        "group": ScheduleGroup,
        "room": ScheduleRoom,
        "teacher": ScheduleTeacher,
        "discipline": ScheduleDiscipline,
    }
    if kind not in models:
        raise ValueError("Неизвестный справочник")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
        raise ValueError("Размер страницы должен быть от 1 до 200")
    if after_id is not None and (not isinstance(after_id, str) or not after_id or len(after_id) > 64):
        raise ValueError("Некорректный курсор")
    model = models[kind]
    statement = select(model).order_by(model.source_id).limit(limit + 1)
    if after_id is not None:
        statement = statement.where(model.source_id > after_id)
    rows = cast(list[DictionaryRecord], list((await session.scalars(statement)).all()))
    has_next = len(rows) > limit
    page = rows[:limit]
    return page, page[-1].source_id if has_next else None
