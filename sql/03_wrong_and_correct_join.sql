-- Wrong: every laboratory event is paired with every admission of the patient.
SELECT COUNT(*) AS wrong_subject_only_rows
FROM admissions AS a
JOIN labevents AS l
  ON a.subject_id = l.subject_id;

-- Correct for encounter attribution: patient and admission must both match.
SELECT COUNT(*) AS correct_encounter_rows
FROM admissions AS a
JOIN labevents AS l
  ON a.subject_id = l.subject_id
 AND a.hadm_id = l.hadm_id;

