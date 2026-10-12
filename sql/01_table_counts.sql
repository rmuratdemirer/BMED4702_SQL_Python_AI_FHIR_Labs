SELECT 'patients' AS table_name, COUNT(*) AS row_count FROM patients
UNION ALL
SELECT 'admissions', COUNT(*) FROM admissions
UNION ALL
SELECT 'd_labitems', COUNT(*) FROM d_labitems
UNION ALL
SELECT 'labevents', COUNT(*) FROM labevents;

