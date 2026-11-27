"""Сохранение подтверждённых полей справочников в БД ЛКС."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher
from app.source.tandem.dictionary_reader import Group, RegistryElement, Room, Teacher


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
