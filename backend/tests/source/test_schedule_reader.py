from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.source.tandem import queries
from app.source.tandem.client import TandemClient
from app.source.tandem.schedule_reader import TandemScheduleReader


@pytest.mark.parametrize(
    ("kind", "query"),
    [
        ("group", queries.SCHEDULE_BY_GROUP),
        ("teacher", queries.SCHEDULE_BY_TEACHER),
        ("room", queries.SCHEDULE_BY_ROOM),
        ("student", queries.SCHEDULE_BY_STUDENT),
    ],
)
async def test_fetch_uses_filter_and_parameters(kind, query):
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [{"id": 5}]
    start, end = date(2026, 1, 1), date(2026, 1, 15)
    result = await TandemScheduleReader(client).fetch(kind, 42, start, end, 20)
    assert result == [{"id": 5}]
    client.fetch.assert_awaited_once_with(query, 42, start, end, 20)


@pytest.mark.parametrize(
    ("kind", "source_id", "start", "end", "limit"),
    [
        ("bad", 1, date(2026, 1, 1), date(2026, 1, 2), 1),
        ("group", 0, date(2026, 1, 1), date(2026, 1, 2), 1),
        ("group", 1, date(2026, 1, 2), date(2026, 1, 1), 1),
        ("group", 1, date(2026, 1, 1), date(2026, 8, 1), 1),
        ("group", 1, date(2026, 1, 1), date(2026, 1, 2), 201),
    ],
)
async def test_invalid_filter_never_queries_source(kind, source_id, start, end, limit):
    client = AsyncMock(spec=TandemClient)
    with pytest.raises(ValueError):
        await TandemScheduleReader(client).fetch(kind, source_id, start, end, limit)
    client.fetch.assert_not_awaited()


async def test_period_limit_counts_both_dates():
    client = AsyncMock(spec=TandemClient)
    reader = TandemScheduleReader(client)
    start = date(2026, 1, 1)
    await reader.fetch("group", 1, start, start + timedelta(days=settings.allowed_period_days - 1))
    client.fetch.assert_awaited_once()
    with pytest.raises(ValueError):
        await reader.fetch("group", 1, start, start + timedelta(days=settings.allowed_period_days))
    assert client.fetch.await_count == 1
