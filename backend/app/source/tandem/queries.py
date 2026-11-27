"""Параметризованные выборки расписания из схемы Тандема.

Аргументы: ID (число), начальная и конечная даты, ограничение строк.
Дата окончания включается целиком. Поля сверены с метаданными БД unisirius.
"""

_BASE = """
SELECT e.id, e.date_p, b.number_p AS bellentrynumber_p, e.starttime_p, e.endtime_p,
       e.activity_p, e.place_p, e.pps_p, e.students_p, e.sysupdatedate_p,
       ARRAY(SELECT DISTINCT p.pps_id FROM ttevent2pps_t p
             WHERE p.event_id = e.id AND p.pps_id IS NOT NULL ORDER BY p.pps_id) AS teacher_ids,
       ARRAY(SELECT DISTINCT p.place_id FROM ttevent2place_t p
             WHERE p.event_id = e.id AND p.place_id IS NOT NULL ORDER BY p.place_id) AS room_ids,
       ARRAY(SELECT DISTINCT g.realedugroup_id FROM ttevent2realedugroup_t g
             WHERE g.event_id = e.id AND g.realedugroup_id IS NOT NULL
             ORDER BY g.realedugroup_id) AS study_group_ids,
       ARRAY(SELECT DISTINCT d.id FROM ttevent2realedugroup_t eg
             JOIN epp_real_edu_group_t g ON g.id = eg.realedugroup_id
             JOIN epp_reg_element_part_t part ON part.id = g.activitypart_id
             JOIN epp_reg_discipline_t d ON d.id = part.registryelement_id
             WHERE eg.event_id = e.id ORDER BY d.id) AS discipline_ids
FROM ttevent_t e
LEFT JOIN sc_bell_entry b ON b.id = e.bellentry_id
JOIN timetableversion_t v ON v.id = e.timetableversion_id
WHERE v.primary_p IS TRUE AND v.archival_p IS FALSE
  AND e.date_p >= $2::date AND e.date_p < ($3::date + 1)
  AND (v.datefrom_p IS NULL OR e.date_p >= v.datefrom_p)
  AND (v.dateto_p IS NULL OR e.date_p <= v.dateto_p)
  AND {filter_condition}
ORDER BY e.date_p, b.number_p, e.id
LIMIT $4
"""

SCHEDULE_BY_TEACHER = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM ttevent2pps_t p WHERE p.event_id = e.id AND p.pps_id = $1
)"""
)
SCHEDULE_BY_ROOM = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM ttevent2place_t p WHERE p.event_id = e.id AND p.place_id = $1
)"""
)
SCHEDULE_BY_STUDENT = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM ttevent2realedugroup_t eg
    JOIN epp_rgrp_row_t r ON r.group_id = eg.realedugroup_id
    WHERE eg.event_id = e.id AND r.student_id = $1
      AND (r.removaldate_p IS NULL OR r.removaldate_p >= e.date_p::date)
)"""
)
SCHEDULE_BY_GROUP = _BASE.format(
    filter_condition="""EXISTS (
    SELECT 1 FROM ttevent2realedugroup_t eg
    JOIN epp_rgrp_row_t r ON r.group_id = eg.realedugroup_id
    JOIN student_t st ON st.id = r.student_id
    WHERE eg.event_id = e.id AND st.group_id = $1
      AND (r.removaldate_p IS NULL OR r.removaldate_p >= e.date_p::date)
)"""
)

GROUP_BY_ID = """
SELECT id, title_p, shorttitle_p, archival_p
FROM group_t
WHERE id = $1
LIMIT 1
"""

ROOM_BY_ID = """
SELECT id, number_p, title_p, cachedbuilding_id
FROM places_place
WHERE id = $1
LIMIT 1
"""

GROUPS_PAGE = """
SELECT id, title_p, shorttitle_p, archival_p
FROM group_t
WHERE ($1::bigint IS NULL OR id > $1)
ORDER BY id
LIMIT $2
"""

ROOMS_PAGE = """
SELECT id, number_p, title_p, cachedbuilding_id
FROM places_place
WHERE ($1::bigint IS NULL OR id > $1)
ORDER BY id
LIMIT $2
"""

TEACHER_BY_ID = """
SELECT t.id, r.guid_p, c.lastname_p, c.firstname_p, c.middlename_p, t.removaldate_p
FROM pps_entry_base_t t
JOIN personrole_t r ON r.id = t.id
LEFT JOIN person_t p ON p.id = r.person_id
LEFT JOIN identitycard_t c ON c.id = p.identitycard_id
WHERE t.id = $1
LIMIT 1
"""

TEACHERS_PAGE = """
SELECT t.id, r.guid_p, c.lastname_p, c.firstname_p, c.middlename_p, t.removaldate_p
FROM pps_entry_base_t t
JOIN personrole_t r ON r.id = t.id
LEFT JOIN person_t p ON p.id = r.person_id
LEFT JOIN identitycard_t c ON c.id = p.identitycard_id
WHERE ($1::bigint IS NULL OR t.id > $1)
ORDER BY t.id
LIMIT $2
"""

TEACHERS_BY_NAME = """
SELECT t.id, r.guid_p, c.lastname_p, c.firstname_p, c.middlename_p, t.removaldate_p
FROM pps_entry_base_t t
JOIN personrole_t r ON r.id = t.id
JOIN person_t p ON p.id = r.person_id
JOIN identitycard_t c ON c.id = p.identitycard_id
WHERE lower(c.firstname_p) = lower($1) AND lower(c.lastname_p) = lower($2)
  AND ($3::bigint IS NULL OR t.id > $3)
ORDER BY t.id
LIMIT $4
"""

REGISTRY_ELEMENTS_PAGE = """
SELECT id, title_p, number_p, usercode_p, guid_p
FROM epp_reg_base_t
WHERE ($1::bigint IS NULL OR id > $1)
ORDER BY id
LIMIT $2
"""

DISCIPLINES_PAGE = """
SELECT b.id, b.title_p, b.number_p, b.usercode_p, b.guid_p
FROM epp_reg_base_t b
JOIN epp_reg_discipline_t d ON d.id = b.id
WHERE ($1::bigint IS NULL OR b.id > $1)
ORDER BY b.id
LIMIT $2
"""

DISCIPLINES_BY_TITLE = """
SELECT b.id, b.title_p, b.number_p, b.usercode_p, b.guid_p
FROM epp_reg_base_t b
JOIN epp_reg_discipline_t d ON d.id = b.id
WHERE strpos(lower(b.title_p), lower($1)) > 0
  AND ($2::bigint IS NULL OR b.id > $2)
ORDER BY b.id
LIMIT $3
"""
