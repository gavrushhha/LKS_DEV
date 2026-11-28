"""Тесты модуля schedule_mapping."""

from datetime import UTC, date, datetime

import pytest

from app.schemas.schedule import ScheduleEntry
from app.source.tandem.mapping import (
    SCHEDULE_COLUMNS,
    map_lesson_type,
    map_schedule_core,
    map_schedule_links,
    minutes_to_time,
    unresolved_schedule_fields,
)


def test_unresolved_fields_are_explicit():
    assert set(unresolved_schedule_fields()) == {
        "week_parity",
        "lesson_type",
        "discipline",
        "group",
        "teacher",
        "room",
        "subgroup",
        "is_cancelled",
        "cancellation_reason",
    }
    assert len({column.api_field for column in SCHEDULE_COLUMNS}) == len(SCHEDULE_COLUMNS)


def test_mapping_lists_every_api_field():
    """Проверить, что ни одно поле ответа не пропущено в описании маппинга."""
    mapped = {column.api_field.split(".")[0] for column in SCHEDULE_COLUMNS}
    assert set(ScheduleEntry.model_fields).issubset(mapped)


@pytest.mark.parametrize(
    ("codes", "expected"),
    [
        (["alt.lectures"], "lecture"),
        (["alt.practice"], "practice"),
        (["alt.labs"], "lab"),
        (["alt.seminars"], "seminar"),
        (["fca.exam"], "exam"),
        (["fca.setoff"], "other"),
        (["fca.controlWork"], "other"),
        (["5"], "consultation"),
        (["6"], "other"),
        ([], None),
        (["unknown"], None),
        (["alt.lectures", "alt.practice"], None),
    ],
)
def test_map_lesson_type_uses_tandem_codes(codes, expected):
    """Преобразовать известный код и не угадывать неоднозначные значения."""
    assert map_lesson_type(codes) == expected


def test_schedule_links_preserve_ids_and_reject_invalid_values():
    assert map_schedule_links(
        {"teacher_ids": [123], "room_ids": [456, 789], "study_group_ids": [10], "discipline_ids": [11]}
    ) == (
        ("teacher", "123"),
        ("room", "456"),
        ("room", "789"),
        ("study_group", "10"),
        ("discipline", "11"),
    )
    with pytest.raises(ValueError):
        map_schedule_links(
            {"teacher_ids": [1, 1], "room_ids": [], "study_group_ids": [], "discipline_ids": []}
        )
    with pytest.raises(ValueError):
        map_schedule_links(
            {"teacher_ids": [], "room_ids": [True], "study_group_ids": [], "discipline_ids": []}
        )


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
        "lesson_type_codes": ["alt.practice"],
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
    assert result.lesson_type == "practice"
    assert result.source_lesson_type_codes == ("alt.practice",)
    assert result.updated_at is None


def test_map_schedule_core_preserves_missing_pair():
    """Сохранить отсутствие номера пары для события без звонка."""
    row = {
        "id": 1,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": None,
        "starttime_p": 525,
        "endtime_p": 605,
        "sysupdatedate_p": None,
    }
    assert map_schedule_core(row, datetime.now(UTC)).pair_number is None


def test_map_schedule_core_preserves_unmapped_source_codes():
    """Сохранить исходный код, даже если он не сопоставлен с API."""
    row = {
        "id": 1,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": None,
        "starttime_p": 720,
        "endtime_p": 750,
        "sysupdatedate_p": None,
        "lesson_type_codes": ["fca.unmapped"],
    }
    result = map_schedule_core(row, datetime.now(UTC))
    assert result.lesson_type is None
    assert result.source_lesson_type_codes == ("fca.unmapped",)


@pytest.mark.parametrize("pair", [0, -1, True, "1"])
def test_map_schedule_core_rejects_invalid_pair(pair):
    """Отклонить некорректный номер пары."""
    row = {
        "id": 1,
        "date_p": date(2026, 12, 7),
        "bellentrynumber_p": pair,
        "starttime_p": 525,
        "endtime_p": 605,
        "sysupdatedate_p": None,
    }
    with pytest.raises(ValueError, match="номер пары"):
        map_schedule_core(row, datetime.now(UTC))
