SELECT
    l.labevent_id,
    l.subject_id,
    l.hadm_id,
    l.specimen_id,
    l.charttime,
    l.storetime,
    ROUND((julianday(l.storetime) - julianday(l.charttime)) * 1440.0, 1)
        AS availability_minutes,
    l.itemid,
    d.label,
    d.fluid,
    l.valuenum,
    l.valueuom,
    l.ref_range_lower,
    l.ref_range_upper,
    l.flag,
    l.priority
FROM labevents AS l
JOIN d_labitems AS d
  ON d.itemid = l.itemid
WHERE l.subject_id = :subject_id
  AND l.hadm_id = :hadm_id
  AND l.itemid = :itemid
  AND l.valuenum IS NOT NULL
ORDER BY l.charttime, l.labevent_id;
