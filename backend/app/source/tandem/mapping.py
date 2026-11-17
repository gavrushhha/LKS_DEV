"""Декларативный маппинг «источник → модель API» (ТЗ, 5.4).

Все имена таблиц и колонок собраны здесь, чтобы изменение схемы источника
правилось в одном файле. Значения помечены «уточнить» до получения схемы
от владельца Тандема (открытые вопросы 1–5 в ТЗ).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMap:
    source_table: str
    source_column: str
    api_field: str
    note: str = ""


SCHEDULE_COLUMNS: tuple[ColumnMap, ...] = (
    ColumnMap("schedule_entry", "id", "id", "уточнить имя PK"),
    ColumnMap("schedule_entry", "study_date", "date", "уточнить имя"),
    ColumnMap("schedule_entry", "pair_no", "pair_number", "уточнить имя"),
    ColumnMap("schedule_entry", "week_parity", "week_parity", "числитель/знаменатель"),
    ColumnMap("schedule_entry", "lesson_kind_id", "lesson_type", "маппинг вида занятия"),
    ColumnMap("schedule_entry", "subgroup_no", "subgroup", "уточнить наличие"),
    ColumnMap("schedule_entry", "is_cancelled", "is_cancelled", "уточнить наличие"),
    ColumnMap("schedule_entry", "cancel_reason", "cancellation_reason", "уточнить наличие"),
    ColumnMap("schedule_entry", "updated_at", "source.updated_at", "критично для дельты"),
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
