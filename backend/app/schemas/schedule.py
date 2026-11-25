"""Схемы расписания (ТЗ, 4.3)."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.core.config import settings
from app.schemas.common import PageMeta, Ref


class SourceInfo(BaseModel):
    system: str = "tandem"
    updated_at: datetime | None = None
    fetched_at: datetime | None = None


class ScheduleEntry(BaseModel):
    """Занятие расписания — read-only проекция источника."""

    id: str
    date: date
    pair_number: int
    starts_at: str | None = None
    ends_at: str | None = None
    week_parity: Literal["odd", "even", "every"] = "every"
    lesson_type: str | None = None
    discipline: Ref | None = None
    group: Ref | None = None
    teacher: Ref | None = None
    room: Ref | None = None
    subgroup: int | None = None
    is_cancelled: bool = False
    cancellation_reason: str | None = None
    source: SourceInfo = SourceInfo()


class ScheduleList(BaseModel):
    items: list[ScheduleEntry] = []
    meta: PageMeta = PageMeta()


class SourceStatus(BaseModel):
    """Состояние источника расписания (ТЗ, 5.5)."""

    mode: Literal["replica", "snapshot"]
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    lag_seconds: int | None = None
    is_stale: bool = True
    source_schema_version: str | None = None
    last_error: str | None = None

    @classmethod
    def from_settings(cls) -> "SourceStatus":
        return cls(mode=settings.tandem_mode, is_stale=True, last_error="источник ещё не опрашивался")
