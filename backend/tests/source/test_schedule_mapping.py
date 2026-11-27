"""Тесты модуля schedule_mapping."""

from datetime import UTC, date, datetime

import pytest

from app.source.tandem.mapping import (
    SCHEDULE_COLUMNS,
    map_schedule_core,
    minutes_to_time,
    unresolved_schedule_fields,
)


def test_unresolved_fields_are_explicit():
    assert set(unresolved_schedule_fields()) == {
        "week_parity",
        "subgroup",
        "is_cancelled",
        "cancellation_reason",
    }
    assert len({column.api_field for column in SCHEDULE_COLUMNS}) == len(SCHEDULE_COLUMNS)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(525, "08:45"), (605, "10:05"), (715, "11:55"), (795, "13:15"), (0, "00:00"), (1439, "23:59")],
)
def test_minutes_to_time(value, expected):
    assert minutes_to_time(value) == expected


def test_minutes_to_time_preserves_missing_and_rejects_invalid():
    assert minutes_to_time(None) is None
    for value in (-1, 1440, True):
        with pytest.raises(ValueError):
            minutes_to_time(value)


def test_map_schedule_core_preserves_source_id_and_converts_time():
    row = {
        "id": 1840889078541792895,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": 1,
        "starttime_p": 525,
        "endtime_p": 605,
        "sysupdatedate_p": None,
    }
    fetched = datetime(2026, 12, 7, tzinfo=UTC)
    result = map_schedule_core(row, fetched)
    assert result.id == "1840889078541792895"
    assert (result.date, result.pair_number, result.starts_at, result.ends_at) == (
        date(2026, 12, 7),
        1,
        "08:45",
        "10:05",
    )
    assert result.fetched_at == fetched
    assert result.updated_at is None


def test_map_schedule_core_rejects_missing_pair():
    row = {
        "id": 1,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": None,
        "starttime_p": 525,
        "endtime_p": 605,
        "sysupdatedate_p": None,
    }
    with pytest.raises(ValueError, match="номер пары"):
        map_schedule_core(row, datetime.now(UTC))
