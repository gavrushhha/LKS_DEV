"""Доменные правила журнала (ТЗ, 6.2). Реализация — T8/T11."""

from datetime import date, datetime, timedelta

EDIT_WINDOW_DAYS = 30
COMMENT_REQUIRED_AFTER_HOURS = 24
MIN_COMMENT_LENGTH = 10


def within_edit_window(lesson_date: date, today: date) -> bool:
    """Правка разрешена в течение 30 дней после даты занятия."""
    return (today - lesson_date) <= timedelta(days=EDIT_WINDOW_DAYS)


def comment_required(
    grade_created_at: datetime, now: datetime, new_value: str, old_value: str | None
) -> bool:
    """Комментарий обязателен: позже 24 ч или при понижении оценки."""
    if old_value is not None and new_value < old_value:
        return True
    return (now - grade_created_at).total_seconds() > COMMENT_REQUIRED_AFTER_HOURS * 3600
