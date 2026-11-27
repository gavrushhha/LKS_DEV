"""Маппинг полей Тандема в модель расписания."""
# Все имена таблиц и колонок собраны здесь, чтобы изменение схемы источника
# правилось в одном файле. Значения помечены «уточнить» до получения схемы
# от владельца Тандема (открытые вопросы 1–5 в ТЗ).

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class ColumnMap:
    """Соответствие поля источника и поля API."""

    source_table: str | None
    source_column: str | None
    api_field: str
    note: str = ""


SCHEDULE_COLUMNS: tuple[ColumnMap, ...] = (
    ColumnMap("ttevent_t", "id", "id", "идентификатор источника"),
    ColumnMap("ttevent_t", "date_p", "date"),
    ColumnMap("sc_bell_entry", "number_p", "pair_number", "связь через bellentry_id"),
    ColumnMap("ttevent_t", "starttime_p", "starts_at", "минуты от полуночи; сверено на примере"),
    ColumnMap("ttevent_t", "endtime_p", "ends_at", "минуты от полуночи; сверено на примере"),
    ColumnMap(None, None, "week_parity", "способ определения не подтверждён"),
    ColumnMap(None, None, "lesson_type", "связь и значения не подтверждены"),
    ColumnMap(
        "ttevent_t", "activity_p", "discipline", "текст; в проверенной выборке NULL; ID не подтверждён"
    ),
    ColumnMap(
        "ttevent_t", "students_p", "group", "текст; в проверенной выборке NULL; связь с группой отдельно"
    ),
    ColumnMap("ttevent_t", "pps_p", "teacher", "текст; в проверенной выборке NULL"),
    ColumnMap("ttevent_t", "place_p", "room", "текст; ID помещения получается через ttevent2place_t"),
    ColumnMap("ttevent2pps_t", "pps_id", "teacher.source_ids", "связь по event_id; может быть несколько"),
    ColumnMap("ttevent2place_t", "place_id", "room.source_ids", "связь по event_id; может быть несколько"),
    ColumnMap(
        "ttevent2realedugroup_t",
        "realedugroup_id",
        "study_group.source_ids",
        "учебная группа, не академическая",
    ),
    ColumnMap(
        "epp_reg_element_part_t",
        "registryelement_id",
        "discipline.source_ids",
        "через учебную группу и epp_reg_discipline_t; проверено на одной группе",
    ),
    ColumnMap(None, None, "subgroup", "источник не подтверждён"),
    ColumnMap(None, None, "is_cancelled", "признак отмены не подтверждён"),
    ColumnMap(None, None, "cancellation_reason", "источник не подтверждён"),
    ColumnMap(None, None, "source.system", "константа приложения"),
    ColumnMap(
        "ttevent_t", "sysupdatedate_p", "source.updated_at", "не учитывает изменения связанных записей"
    ),
    ColumnMap(None, None, "source.fetched_at", "время чтения приложением"),
)

LESSON_TYPE_MAP: dict[str, str] = {
    # TODO(T2.2): заполнить по справочнику видов занятий источника
    "LECTURE": "lecture",
    "PRACTICE": "practice",
    "LAB": "lab",
    "SEMINAR": "seminar",
    "EXAM": "exam",
    "CONSULT": "consultation",
}


def unresolved_schedule_fields() -> tuple[str, ...]:
    """Получить поля расписания с неподтверждённым источником."""
    # source.system и source.fetched_at формируются приложением, а не читаются из БД.
    generated = {"source.system", "source.fetched_at"}
    return tuple(
        column.api_field
        for column in SCHEDULE_COLUMNS
        if column.source_table is None and column.api_field not in generated
    )


def minutes_to_time(value: int | None) -> str | None:
    """Преобразовать минуты от полуночи в формат HH:MM."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 24 * 60:
        raise ValueError("Время должно быть числом минут от 0 до 1439")
    hours, minutes = divmod(value, 60)
    return f"{hours:02d}:{minutes:02d}"


def map_schedule_links(row: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    """Преобразовать проверенные ID преподавателей и аудиторий в строки."""
    links: list[tuple[str, str]] = []
    for field, kind in (
        ("teacher_ids", "teacher"),
        ("room_ids", "room"),
        ("study_group_ids", "study_group"),
        ("discipline_ids", "discipline"),
    ):
        values = row[field]
        if not isinstance(values, list) or any(
            isinstance(value, bool) or not isinstance(value, int) or not 0 < value < 2**63 for value in values
        ):
            raise ValueError("Некорректные идентификаторы связей занятия")
        if len(set(values)) != len(values):
            raise ValueError("Повторяющиеся связи занятия")
        links.extend((kind, str(value)) for value in values)
    return tuple(links)


@dataclass(frozen=True)
class ScheduleCore:
    """Подтверждённые поля занятия; это ещё не полный ответ API."""

    id: str
    date: date
    pair_number: int
    starts_at: str | None
    ends_at: str | None
    updated_at: datetime | None
    fetched_at: datetime


def map_schedule_core(row: Mapping[str, Any], fetched_at: datetime) -> ScheduleCore:
    """Преобразовать подтверждённые поля источника без значения по умолчанию для неизвестных."""
    source_id = row["id"]
    lesson_date = row["date_p"]
    pair = row["bellentrynumber_p"]
    updated_at = row["sysupdatedate_p"]
    if isinstance(source_id, bool) or not isinstance(source_id, int):
        raise ValueError("Некорректный идентификатор занятия")
    if not isinstance(lesson_date, date) or isinstance(lesson_date, datetime):
        raise ValueError("Некорректная дата занятия")
    if isinstance(pair, bool) or not isinstance(pair, int) or pair < 1:
        raise ValueError("Не указан корректный номер пары")
    if updated_at is not None and not isinstance(updated_at, datetime):
        raise ValueError("Некорректное время обновления источника")
    if fetched_at.tzinfo is None or fetched_at.utcoffset() is None:
        raise ValueError("Время чтения должно содержать часовой пояс")
    return ScheduleCore(
        id=str(source_id),
        date=lesson_date,
        pair_number=pair,
        starts_at=minutes_to_time(row["starttime_p"]),
        ends_at=minutes_to_time(row["endtime_p"]),
        updated_at=updated_at,
        fetched_at=fetched_at,
    )
