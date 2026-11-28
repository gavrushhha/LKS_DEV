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
    complete: bool = True


SCHEDULE_COLUMNS: tuple[ColumnMap, ...] = (
    ColumnMap("ttevent_t", "id", "id", "идентификатор источника"),
    ColumnMap("ttevent_t", "date_p", "date"),
    ColumnMap("sc_bell_entry", "number_p", "pair_number", "связь через bellentry_id"),
    ColumnMap("ttevent_t", "starttime_p", "starts_at", "минуты от полуночи; сверено на примере"),
    ColumnMap("ttevent_t", "endtime_p", "ends_at", "минуты от полуночи; сверено на примере"),
    ColumnMap(None, None, "week_parity", "способ определения не подтверждён"),
    ColumnMap(
        "epp_group_type_t",
        "code_p",
        "lesson_type",
        "не все коды сопоставлены; связь через учебную группу",
        False,
    ),
    ColumnMap(
        "ttevent_t",
        "activity_p",
        "discipline",
        "текст может отсутствовать; полная ссылка требует справочника",
        False,
    ),
    ColumnMap(
        "ttevent_t", "students_p", "group", "текст может отсутствовать; состав групп требует проверки", False
    ),
    ColumnMap(
        "ttevent_t", "pps_p", "teacher", "текст может отсутствовать; полная ссылка требует справочника", False
    ),
    ColumnMap(
        "ttevent_t",
        "place_p",
        "room",
        "ID получается через ttevent2place_t; полная ссылка не завершена",
        False,
    ),
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
    "alt.lectures": "lecture",
    "alt.practice": "practice",
    "alt.labs": "lab",
    "alt.seminars": "seminar",
    "fca.exam": "exam",
    "fca.setoff": "other",
    "fca.controlWork": "other",
    "5": "consultation",
    "6": "other",
}


def unresolved_schedule_fields() -> tuple[str, ...]:
    """Получить поля с отсутствующим или неполным маппингом."""
    # source.system и source.fetched_at формируются приложением, а не читаются из БД.
    generated = {"source.system", "source.fetched_at"}
    return tuple(
        column.api_field
        for column in SCHEDULE_COLUMNS
        if (column.source_table is None or not column.complete) and column.api_field not in generated
    )


def minutes_to_time(value: int | None) -> str | None:
    """Преобразовать минуты от полуночи в формат HH:MM."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 24 * 60:
        raise ValueError("Время должно быть числом минут от 0 до 1439")
    hours, minutes = divmod(value, 60)
    return f"{hours:02d}:{minutes:02d}"


def map_lesson_type(codes: list[str] | None) -> str | None:
    """Преобразовать однозначный вид занятия из подтверждённых кодов Тандема."""
    if codes is None or codes == []:
        return None
    if not isinstance(codes, list) or any(not isinstance(code, str) for code in codes):
        raise ValueError("Некорректные коды вида занятия")
    mapped = [LESSON_TYPE_MAP.get(code) for code in codes]
    if any(value is None for value in mapped) or len(set(mapped)) != 1:
        return None
    return mapped[0]


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
    pair_number: int | None
    starts_at: str | None
    ends_at: str | None
    updated_at: datetime | None
    fetched_at: datetime
    lesson_type: str | None = None
    source_lesson_type_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScheduleReference:
    """Ссылка источника с названием, если оно найдено."""

    kind: str
    source_id: str
    name: str | None


@dataclass(frozen=True)
class ScheduleProjection:
    """Данные занятия Тандема без подстановки неизвестных значений."""

    core: ScheduleCore
    references: tuple[ScheduleReference, ...]
    activity_text: str | None
    teachers_text: str | None
    groups_text: str | None
    place_text: str | None
    week_parity: str | None = None
    subgroup: int | None = None
    is_cancelled: bool | None = None
    cancellation_reason: str | None = None


def map_schedule_projection(
    row: Mapping[str, Any], fetched_at: datetime, names: Mapping[tuple[str, str], str | None]
) -> ScheduleProjection:
    """Сопоставить поля занятия и все подтверждённые ссылки источника."""
    texts = [row[key] for key in ("activity_p", "pps_p", "students_p", "place_p")]
    if any(text is not None and not isinstance(text, str) for text in texts):
        raise ValueError("Некорректное текстовое поле занятия")
    return ScheduleProjection(
        core=map_schedule_core(row, fetched_at),
        references=tuple(
            ScheduleReference(kind=kind, source_id=source_id, name=names.get((kind, source_id)))
            for kind, source_id in map_schedule_links(row)
        ),
        activity_text=texts[0],
        teachers_text=texts[1],
        groups_text=texts[2],
        place_text=texts[3],
    )


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
    if pair is not None and (isinstance(pair, bool) or not isinstance(pair, int) or pair < 1):
        raise ValueError("Некорректный номер пары")
    if updated_at is not None and not isinstance(updated_at, datetime):
        raise ValueError("Некорректное время обновления источника")
    if fetched_at.tzinfo is None or fetched_at.utcoffset() is None:
        raise ValueError("Время чтения должно содержать часовой пояс")
    type_codes = row.get("lesson_type_codes")
    mapped_type = map_lesson_type(type_codes)
    return ScheduleCore(
        id=str(source_id),
        date=lesson_date,
        pair_number=pair,
        starts_at=minutes_to_time(row["starttime_p"]),
        ends_at=minutes_to_time(row["endtime_p"]),
        updated_at=updated_at,
        fetched_at=fetched_at,
        lesson_type=mapped_type,
        source_lesson_type_codes=tuple(type_codes) if type_codes is not None else (),
    )
