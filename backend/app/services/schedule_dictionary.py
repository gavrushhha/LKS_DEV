"""Сохранение подтверждённых полей справочников в БД ЛКС."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher
from app.source.tandem.dictionary_reader import Group, RegistryElement, Room, TandemDictionaryReader, Teacher


@dataclass(frozen=True)
class DictionarySyncProgress:
    """Число сохранённых страниц и точка продолжения ограниченной загрузки."""

    pages: int
    records: int
    next_after_id: int | None
    complete: bool


class DictionarySyncError(Exception):
    """Ошибка загрузки с положением после последней сохранённой страницы."""

    def __init__(self, progress: DictionarySyncProgress) -> None:
        super().__init__("Не удалось загрузить страницу справочника")
        self.progress = progress


async def save_schedule_dictionary_item(session: AsyncSession, item: Group | Room | Teacher) -> None:
    """Добавить или обновить одну запись в текущей транзакции БД ЛКС."""
    obj: ScheduleGroup | ScheduleRoom | ScheduleTeacher
    if isinstance(item, Group):
        obj = ScheduleGroup(
            source_id=item.id, title=item.title, short_title=item.short_title, archived=item.archived
        )
    elif isinstance(item, Room):
        obj = ScheduleRoom(
            source_id=item.id, number=item.number, title=item.title, building_source_id=item.building_id
        )
    elif isinstance(item, Teacher):
        obj = ScheduleTeacher(
            source_id=item.id,
            role_guid=item.role_guid,
            last_name=item.last_name,
            first_name=item.first_name,
            middle_name=item.middle_name,
            removal_date=item.removal_date,
        )
    else:
        raise TypeError("Неподдерживаемый тип справочника")
    await session.merge(obj)


async def save_schedule_discipline(session: AsyncSession, item: RegistryElement) -> None:
    """Сохранить запись только после чтения из справочника дисциплин, а не всего реестра."""
    await session.merge(
        ScheduleDiscipline(
            source_id=item.id,
            title=item.title,
            number=item.number,
            user_code=item.user_code,
            source_guid=item.guid,
        )
    )


async def sync_dictionary_page(
    reader: TandemDictionaryReader,
    session: AsyncSession,
    kind: Literal["group", "room", "teacher", "discipline"],
    *,
    after_id: int | None = None,
    limit: int = 100,
) -> tuple[int, int | None]:
    """Загрузить одну страницу и вернуть число записей и курсор следующей страницы."""
    entries: Sequence[Group | Room | Teacher | RegistryElement]
    if kind == "group":
        entries = await reader.groups_page(after_id=after_id, limit=limit)
    elif kind == "room":
        entries = await reader.rooms_page(after_id=after_id, limit=limit)
    elif kind == "teacher":
        entries = await reader.teachers_page(after_id=after_id, limit=limit)
    elif kind == "discipline":
        entries = await reader.disciplines_page(after_id=after_id, limit=limit)
    else:
        raise ValueError("Неизвестный справочник")

    expected_type = {"group": Group, "room": Room, "teacher": Teacher, "discipline": RegistryElement}[kind]
    if any(not isinstance(entry, expected_type) for entry in entries):
        raise ValueError("Тип записи не соответствует справочнику")
    ids = [int(entry.id) for entry in entries]
    if (
        any(i <= 0 or i >= 2**63 or (after_id is not None and i <= after_id) for i in ids)
        or ids != sorted(set(ids))
        or len(ids) > limit
    ):
        raise ValueError("Некорректная страница справочника")
    async with session.begin():
        for entry in entries:
            if isinstance(entry, RegistryElement):
                await save_schedule_discipline(session, entry)
            else:
                await save_schedule_dictionary_item(session, entry)
    return len(entries), ids[-1] if len(entries) == limit else None


async def sync_dictionary_batch(
    reader: TandemDictionaryReader,
    session: AsyncSession,
    kind: Literal["group", "room", "teacher", "discipline"],
    *,
    after_id: int | None = None,
    page_size: int = 100,
    max_pages: int = 5,
) -> DictionarySyncProgress:
    """Загрузить ограниченное число страниц; каждая страница сохраняется отдельно."""
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= 10:
        raise ValueError("Число страниц должно быть от 1 до 10")
    pages, records, cursor = 0, 0, after_id
    while pages < max_pages:
        try:
            count, next_cursor = await sync_dictionary_page(
                reader, session, kind, after_id=cursor, limit=page_size
            )
        except Exception as exc:
            raise DictionarySyncError(DictionarySyncProgress(pages, records, cursor, False)) from exc
        pages += 1
        records += count
        if next_cursor is None:
            return DictionarySyncProgress(pages, records, None, True)
        cursor = next_cursor
    return DictionarySyncProgress(pages, records, cursor, False)
