"""Ограниченные выборки расписания из источника Тандема.

Результат содержит поля источника; преобразование в API пока не реализовано.
"""

from datetime import UTC, date, datetime
from typing import Any, Literal

from app.core.config import settings
from app.source.tandem import queries
from app.source.tandem.client import TandemClient
from app.source.tandem.mapping import ScheduleCore, map_schedule_core

FilterKind = Literal["group", "teacher", "room", "student"]
_QUERIES = {
    "group": queries.SCHEDULE_BY_GROUP,
    "teacher": queries.SCHEDULE_BY_TEACHER,
    "room": queries.SCHEDULE_BY_ROOM,
    "student": queries.SCHEDULE_BY_STUDENT,
}


class TandemScheduleReader:
    def __init__(self, client: TandemClient) -> None:
        self._client = client

    async def fetch(
        self, kind: FilterKind, source_id: int, date_from: date, date_to: date, limit: int = 50
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
        self, kind: FilterKind, source_id: int, date_from: date, date_to: date, limit: int = 50
    ) -> list[ScheduleCore]:
        """Получить и преобразовать подтверждённые поля после чтения источника."""
        rows = await self.fetch(kind, source_id, date_from, date_to, limit)
        fetched_at = datetime.now(UTC)
        return [map_schedule_core(row, fetched_at) for row in rows]
