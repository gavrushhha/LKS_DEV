"""Тесты модуля schedule_reader."""

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


async def test_fetch_core_converts_rows_from_source():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {
            "id": 123,
            "date_p": date(2026, 12, 7),
            "bellentrynumber_p": 1,
            "starttime_p": 525,
            "endtime_p": 605,
            "sysupdatedate_p": None,
        }
    ]
    result = await TandemScheduleReader(client).fetch_core("group", 42, date(2026, 12, 7), date(2026, 12, 7))
    assert len(result) == 1
    assert (result[0].id, result[0].starts_at, result[0].ends_at) == ("123", "08:45", "10:05")
    assert result[0].fetched_at.utcoffset() == timedelta(0)


async def test_fetch_mapped_preserves_all_links_and_unknown_fields():
    """Проверить пакетное чтение названий и отсутствие выдуманных значений."""
    client = AsyncMock(spec=TandemClient)
    source = {
        "id": 123,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": None,
        "starttime_p": 720,
        "endtime_p": 750,
        "sysupdatedate_p": None,
        "lesson_type_codes": ["6"],
        "activity_p": None,
        "pps_p": None,
        "students_p": None,
        "place_p": None,
        "teacher_ids": [11, 12],
        "room_ids": [21],
        "study_group_ids": [31],
        "discipline_ids": [41],
    }
    client.fetch.side_effect = [
        [source],
        [
            {"kind": "teacher", "source_id": 11, "name": "Преподаватель"},
            {"kind": "room", "source_id": 21, "name": "101"},
            {"kind": "study_group", "source_id": 31, "name": "Поток"},
            {"kind": "discipline", "source_id": 41, "name": "Дисциплина"},
        ],
    ]
    result = await TandemScheduleReader(client).fetch_mapped(
        "group", 42, date(2026, 12, 7), date(2026, 12, 7)
    )
    item = result[0]
    assert item.core.pair_number is None and item.core.lesson_type == "other"
    assert item.week_parity is None and item.is_cancelled is None and item.subgroup is None
    assert {(x.kind, x.source_id, x.name) for x in item.references} == {
        ("teacher", "11", "Преподаватель"),
        ("teacher", "12", None),
        ("room", "21", "101"),
        ("study_group", "31", "Поток"),
        ("discipline", "41", "Дисциплина"),
    }
    assert client.fetch.await_args_list[1].args == (
        queries.SCHEDULE_REFERENCE_NAMES,
        [11, 12],
        [21],
        [31],
        [41],
    )


async def test_fetch_mapped_empty_result_uses_one_query():
    """Не обращаться к справочникам при отсутствии занятий."""
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = []
    assert (
        await TandemScheduleReader(client).fetch_mapped("group", 42, date(2026, 12, 7), date(2026, 12, 7))
        == []
    )
    assert client.fetch.await_count == 1
