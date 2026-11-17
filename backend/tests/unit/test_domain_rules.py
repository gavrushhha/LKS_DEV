"""Доменные правила журнала (ТЗ, 6.2)."""

from datetime import date, datetime, timedelta

from app.domain.rules import comment_required, within_edit_window


def test_edit_window_allows_recent_lesson() -> None:
    assert within_edit_window(date(2027, 3, 1), date(2027, 3, 20))


def test_edit_window_blocks_old_lesson() -> None:
    assert not within_edit_window(date(2027, 1, 1), date(2027, 3, 20))


def test_comment_required_after_24h() -> None:
    created = datetime(2027, 3, 1, 9, 0)
    now = created + timedelta(hours=30)
    assert comment_required(created, now, "5", "5")


def test_comment_not_required_within_24h() -> None:
    created = datetime(2027, 3, 1, 9, 0)
    now = created + timedelta(hours=2)
    assert not comment_required(created, now, "5", "5")
