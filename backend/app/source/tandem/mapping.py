"""Декларативный маппинг «источник → модель API» (ТЗ, 5.4).

Все имена таблиц и колонок собраны здесь, чтобы изменение схемы источника
правилось в одном файле. Значения помечены «уточнить» до получения схемы
от владельца Тандема (открытые вопросы 1–5 в ТЗ).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class ColumnMap:
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
    ColumnMap("epp_group_type_t", "title_p", "lesson_type", "значения справочника не подтверждены"),
    ColumnMap("ttevent_t", "activity_p", "discipline", "только название; ID через связи"),
    ColumnMap("ttevent_t", "students_p", "group", "только названия; ID через связи"),
    ColumnMap("ttevent_t", "pps_p", "teacher", "только имена; ID через связи"),
    ColumnMap("ttevent_t", "place_p", "room", "только названия; ID через связи"),
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
    """Вернуть поля, для которых пока не указан источник в БД.

    source.system и source.fetched_at формируются приложением, а не читаются из БД.
    """
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
