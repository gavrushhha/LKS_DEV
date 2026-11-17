"""Чтение расписания: кэш → источник (ТЗ, 5.5)."""

from datetime import date

from app.core.config import settings
from app.core.deps import User
from app.schemas.schedule import ScheduleList


class ScheduleService:
    """Слой чтения расписания. Реальная реализация — задачи T2/T3/T4."""

    async def get_schedule(self, user: User, date_from: date, date_to: date) -> ScheduleList:
        # TODO(T4.1): проверить обязательные фильтры и период (<=92 дней)
        # TODO(T3.1): попытаться отдать из Redis по ключу (фильтры, период, роль)
        # TODO(T2.3): SELECT к реплике Тандема через app/source/tandem/queries.py
        # TODO(T3.3): при недоступности источника — снимок + заголовок X-Data-Stale
        _ = (user, date_from, date_to, settings.schedule_cache_ttl_seconds)
        return ScheduleList()
