"""Параметризованные выборки расписания из схемы Тандема.

Аргументы: ID (число), начальная и конечная даты, ограничение строк.
Дата окончания включается целиком. Имена и связи взяты из dbstruct-_2_.csv.
"""

_BASE = """
SELECT e.id, e.date_p, e.bellentrynumber_p, e.starttime_p, e.endtime_p,
       e.activity_p, e.place_p, e.pps_p, e.students_p, e.incorrect_p,
       e.lockstate_id, s.sysupdatedate_p
FROM timetableevent_t e
JOIN sc_event s ON s.id = e.id
JOIN timetableversion_t v ON v.id = e.timetableversion_id
WHERE v.primary_p IS TRUE AND v.archival_p IS FALSE
  AND e.date_p >= $2::date AND e.date_p < ($3::date + 1)
  AND e.date_p >= v.datefrom_p AND e.date_p < (v.dateto_p::date + 1)
  AND {filter_condition}
ORDER BY e.date_p, e.bellentrynumber_p, e.id
LIMIT $4
"""

SCHEDULE_BY_TEACHER = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM ttevent2pps_t p WHERE p.event_id = e.id AND p.pps_id = $1
)"""
)
SCHEDULE_BY_ROOM = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM sc_event_place p WHERE p.scheduleevent_id = e.id AND p.place_id = $1
)"""
)
SCHEDULE_BY_STUDENT = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM tteventreal2edugroup_t eg
    JOIN epp_rgrp_row_t r ON r.group_id = eg.realedugroup_id
    WHERE eg.event_id = e.id AND r.student_id = $1
      AND (r.removaldate_p IS NULL OR r.removaldate_p >= e.date_p::date)
)"""
)
SCHEDULE_BY_GROUP = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM tteventreal2edugroup_t eg
    JOIN epp_rgrp_row_t r ON r.group_id = eg.realedugroup_id
    JOIN student_t st ON st.id = r.student_id
    WHERE eg.event_id = e.id AND st.group_id = $1
      AND (r.removaldate_p IS NULL OR r.removaldate_p >= e.date_p::date)
)"""
)
