-- Week 2 - source evidence for a FHIR Observation transformation
-- Local item coding is retained; no LOINC equivalence is invented.
SELECT
    le.labevent_id,
    le.subject_id,
    le.hadm_id,
    le.itemid,
    di.label,
    di.fluid,
    le.charttime,
    le.storetime,
    le.valuenum,
    le.valueuom,
    le.flag
FROM labevents AS le
JOIN d_labitems AS di ON di.itemid = le.itemid
WHERE lower(di.label) = 'creatinine'
  AND le.valuenum IS NOT NULL
ORDER BY le.subject_id, le.charttime
LIMIT 100;
