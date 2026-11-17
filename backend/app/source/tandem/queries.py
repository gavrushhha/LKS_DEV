"""SQL-выборки расписания. Только SELECT (ТЗ, 5.6).

Каждый запрос ограничен фильтром (группа/преподаватель/аудитория) и периодом.
Полный дамп расписания запрещён.
"""

SCHEDULE_BY_GROUP = """
-- TODO(T2.3): уточнить имена таблиц и колонок
SELECT e.id,
       e.study_date,
       e.pair_no,
       e.week_parity,
       e.lesson_kind_id,
       e.subgroup_no,
       e.updated_at
FROM schedule_entry e
WHERE e.group_id = $1
  AND e.study_date BETWEEN $2 AND $3
ORDER BY e.study_date, e.pair_no
LIMIT $4
"""

SCHEDULE_BY_TEACHER = """
SELECT e.id, e.study_date, e.pair_no, e.week_parity, e.updated_at
FROM schedule_entry e
WHERE e.teacher_id = $1
  AND e.study_date BETWEEN $2 AND $3
ORDER BY e.study_date, e.pair_no
LIMIT $4
"""
