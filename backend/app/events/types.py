"""Реестр типов событий (ТЗ, 8.2)."""

LESSON_CREATED = "lesson.created"
GRADE_CREATED = "grade.created"
GRADE_UPDATED = "grade.updated"
ATTENDANCE_MARKED = "attendance.marked"
STATEMENT_FORMED = "statement.formed"
STATEMENT_CLOSED = "statement.closed"
SCHEDULE_SYNC_COMPLETED = "schedule.sync.completed"
SCHEDULE_SOURCE_DEGRADED = "schedule.source.degraded"

ALL_EVENTS = (
    LESSON_CREATED,
    GRADE_CREATED,
    GRADE_UPDATED,
    ATTENDANCE_MARKED,
    STATEMENT_FORMED,
    STATEMENT_CLOSED,
    SCHEDULE_SYNC_COMPLETED,
    SCHEDULE_SOURCE_DEGRADED,
)
