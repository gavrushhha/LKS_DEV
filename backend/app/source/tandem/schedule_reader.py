"""Ограниченные выборки расписания из источника Тандема."""
# Результат содержит поля источника; преобразование в API пока не реализовано.

from datetime import UTC, date, datetime
from typing import Any, Literal

from app.core.config import settings
from app.source.tandem import queries
from app.source.tandem.client import TandemClient
from app.source.tandem.mapping import (
    ScheduleCore,
    ScheduleProjection,
    map_academic_group_links,
    map_schedule_core,
    map_schedule_links,
    map_schedule_projection,
)

FilterKind = Literal["group", "teacher", "room", "student"]
_QUERIES = {
    "group": queries.SCHEDULE_BY_GROUP,
    "teacher": queries.SCHEDULE_BY_TEACHER,
    "room": queries.SCHEDULE_BY_ROOM,
    "student": queries.SCHEDULE_BY_STUDENT,
}


class TandemScheduleReader:
    """Клиент ограниченных выборок расписания Тандема."""

    def __init__(self, client: TandemClient) -> None:
        self._client = client

    async def fetch(
        self,
        kind: FilterKind,
        source_id: int,
        date_from: date,
        date_to: date,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Получить ограниченный набор строк с одним фильтром и периодом."""
        if kind not in _QUERIES:
            raise ValueError("Неизвестный фильтр расписания")
        if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id <= 0:
            raise ValueError("Идентификатор должен быть положительным целым числом")
        if date_to < date_from or (date_to - date_from).days >= settings.allowed_period_days:
            raise ValueError("Недопустимый период расписания")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("Количество записей должно быть от 1 до 200")
        return await self._client.fetch(_QUERIES[kind], source_id, date_from, date_to, limit)

    async def fetch_core(
        self,
        kind: FilterKind,
        source_id: int,
        date_from: date,
        date_to: date,
        limit: int = 50,
    ) -> list[ScheduleCore]:
        """Получить и преобразовать подтверждённые поля после чтения источника."""
        rows = await self.fetch(kind, source_id, date_from, date_to, limit)
        fetched_at = datetime.now(UTC)
        return [map_schedule_core(row, fetched_at) for row in rows]

    async def fetch_historical_group_ids(self, event_id: int, event_date: date) -> tuple[str, ...]:
        """Получить академические группы по истории на дату занятия."""
        if isinstance(event_id, bool) or not isinstance(event_id, int) or not 0 < event_id < 2**63:
            raise ValueError("Некорректный идентификатор занятия")
        if not isinstance(event_date, date) or isinstance(event_date, datetime):
            raise ValueError("Некорректная дата занятия")
        rows = await self._client.fetch(queries.HISTORICAL_EVENT_GROUPS, event_id, event_date)
        groups = [row["group_id"] for row in rows]
        return tuple(group_id for _, group_id in map_academic_group_links({"academic_group_ids": groups}))

    async def fetch_mapped(
        self,
        kind: FilterKind,
        source_id: int,
        date_from: date,
        date_to: date,
        limit: int = 50,
    ) -> list[ScheduleProjection]:
        """Получить занятия и названия связанных объектов одним дополнительным запросом."""
        rows = await self.fetch(kind, source_id, date_from, date_to, limit)
        groups: dict[str, set[int]] = {
            name: set() for name in ("teacher", "room", "study_group", "discipline", "academic_group")
        }
        for row in rows:
            for link_kind, link_id in (*map_schedule_links(row), *map_academic_group_links(row)):
                groups[link_kind].add(int(link_id))
        names: dict[tuple[str, str], str | None] = {}
        if any(groups.values()):
            records = await self._client.fetch(
                queries.SCHEDULE_REFERENCE_NAMES,
                *(
                    sorted(groups[name])
                    for name in ("teacher", "room", "study_group", "discipline", "academic_group")
                ),
            )
            for record in records:
                link_kind = record["kind"]
                link_id = record["source_id"]
                name = record["name"]
                if link_kind not in groups or link_id not in groups[link_kind]:
                    raise ValueError("Источник вернул постороннюю запись справочника")
                if name is not None and not isinstance(name, str):
                    raise ValueError("Некорректное название записи справочника")
                key = (link_kind, str(link_id))
                if key in names:
                    raise ValueError("Источник вернул повторяющуюся запись справочника")
                names[key] = name
        fetched_at = datetime.now(UTC)
        return [map_schedule_projection(row, fetched_at, names) for row in rows]
