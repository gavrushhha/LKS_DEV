"""Параметризованные запросы к данным Тандема."""
# Аргументы: ID, начальная и конечная даты, ограничение строк.
# Дата окончания включается целиком. Поля сверены с метаданными БД unisirius.

_HISTORICAL_GROUP_ROWS = """
FROM ttevent2realedugroup_t eg
JOIN epp_rgrp_row_t r ON r.group_id = eg.realedugroup_id
JOIN com_abs_history_element_t base ON base.owner_id = r.student_id
JOIN stud_prop_history_element_t h ON h.id = base.id
JOIN studentstatus_t status ON status.id = h.statuslink_id
WHERE eg.event_id = e.id
  AND (r.removaldate_p IS NULL OR r.removaldate_p >= e.date_p)
  AND h.grouplink_id IS NOT NULL
  AND base.datefrom_p::date = (
      SELECT previous.datefrom_p::date
      FROM com_abs_history_element_t previous
      JOIN stud_prop_history_element_t previous_student ON previous_student.id = previous.id
      WHERE previous.owner_id = r.student_id AND previous.datefrom_p < (e.date_p + 1)::timestamp
      ORDER BY previous.datefrom_p DESC LIMIT 1
  )
  AND status.shorttitle_p IN ('а', 'аоб')
  AND NOT EXISTS (
      SELECT 1 FROM excludestuextract_t x
      JOIN abstractstudentextract_t extract ON extract.id = x.id
      WHERE extract.entity_id = r.student_id AND extract.committed_p IS TRUE
        AND x.date_p::date <= e.date_p
  )
  AND NOT EXISTS (
      SELECT 1 FROM excludestulistextract_t x
      JOIN abstractstudentextract_t extract ON extract.id = x.id
      WHERE extract.entity_id = r.student_id AND extract.committed_p IS TRUE
        AND x.excludedate_p::date <= e.date_p
  )
"""

_BASE = """
SELECT e.id, e.date_p, b.number_p AS bellentrynumber_p, e.starttime_p, e.endtime_p,
       e.activity_p, e.place_p, e.pps_p, e.students_p, e.sysupdatedate_p,
       ARRAY(SELECT DISTINCT a.code_p FROM epp_c_week_characteristics_t w
             JOIN epp_c_week_alternation_t a ON a.id = w.alternation_id
             WHERE e.date_p >= w.datefrom_p::date AND e.date_p <= w.dateto_p::date
               AND (v.eppyear_id IS NULL OR w.eppyear_id = v.eppyear_id)
               AND a.code_p IS NOT NULL ORDER BY a.code_p) AS week_alternation_codes,
       ARRAY(SELECT DISTINCT p.pps_id FROM ttevent2pps_t p
             WHERE p.event_id = e.id AND p.pps_id IS NOT NULL ORDER BY p.pps_id) AS teacher_ids,
       ARRAY(SELECT DISTINCT p.place_id FROM ttevent2place_t p
             WHERE p.event_id = e.id AND p.place_id IS NOT NULL ORDER BY p.place_id) AS room_ids,
       ARRAY(SELECT DISTINCT g.realedugroup_id FROM ttevent2realedugroup_t g
             WHERE g.event_id = e.id AND g.realedugroup_id IS NOT NULL
             ORDER BY g.realedugroup_id) AS study_group_ids,
       ARRAY(SELECT DISTINCT h.grouplink_id
             {historical_group_rows}
             ORDER BY h.grouplink_id) AS academic_group_ids,
       ARRAY(SELECT DISTINCT d.id FROM ttevent2realedugroup_t eg
             JOIN epp_real_edu_group_t g ON g.id = eg.realedugroup_id
             JOIN epp_reg_element_part_t part ON part.id = g.activitypart_id
             JOIN epp_reg_discipline_t d ON d.id = part.registryelement_id
             WHERE eg.event_id = e.id ORDER BY d.id) AS discipline_ids,
       ARRAY(SELECT DISTINCT t.code_p FROM ttevent2realedugroup_t eg
             JOIN epp_real_edu_group_t g ON g.id = eg.realedugroup_id
             JOIN epp_group_type_t t ON t.id = g.type_id
             WHERE eg.event_id = e.id AND t.code_p IS NOT NULL
             ORDER BY t.code_p) AS lesson_type_codes
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

_BASE = _BASE.replace("{historical_group_rows}", _HISTORICAL_GROUP_ROWS)

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
    filter_condition="EXISTS (SELECT 1 " + _HISTORICAL_GROUP_ROWS + " AND h.grouplink_id = $1)"
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

SCHEDULE_REFERENCE_NAMES = """
SELECT 'teacher' AS kind, t.id AS source_id,
       NULLIF(trim(concat_ws(' ', c.lastname_p, c.firstname_p, c.middlename_p)), '') AS name
FROM pps_entry_base_t t
JOIN personrole_t r ON r.id = t.id
LEFT JOIN person_t p ON p.id = r.person_id
LEFT JOIN identitycard_t c ON c.id = p.identitycard_id
WHERE t.id = ANY($1::bigint[])
UNION ALL
SELECT 'room', p.id, COALESCE(NULLIF(p.title_p, ''), NULLIF(p.number_p, ''))
FROM places_place p WHERE p.id = ANY($2::bigint[])
UNION ALL
SELECT 'study_group', g.id, NULLIF(g.title_p, '')
FROM epp_real_edu_group_t g WHERE g.id = ANY($3::bigint[])
UNION ALL
SELECT 'academic_group', g.id, COALESCE(NULLIF(g.title_p, ''), NULLIF(g.shorttitle_p, ''))
FROM group_t g WHERE g.id = ANY($5::bigint[])
UNION ALL
SELECT 'discipline', b.id, NULLIF(b.title_p, '')
FROM epp_reg_base_t b JOIN epp_reg_discipline_t d ON d.id = b.id
WHERE b.id = ANY($4::bigint[])
"""

# Чтение групп отдельного занятия по истории студента на дату занятия.
HISTORICAL_EVENT_GROUPS = (
    "SELECT DISTINCT h.grouplink_id AS group_id FROM ttevent_t e {history} "
    "AND e.id = $1 AND e.date_p = $2::date ORDER BY h.grouplink_id"
).replace("{history}", _HISTORICAL_GROUP_ROWS)
