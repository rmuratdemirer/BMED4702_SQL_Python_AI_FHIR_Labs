-- BMED4702 Week 1 — Visible SQL example
-- This file is for reading and discussion in PyCharm/DataGrip.

-- 1) Discover the tables in the SQLite database.
SELECT name AS table_name
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- 2) Count rows in important MIMIC-IV Demo tables.
-- Run each SELECT separately if one of the tables is not present.
SELECT 'patients' AS table_name, COUNT(*) AS row_count FROM patients;
SELECT 'admissions' AS table_name, COUNT(*) AS row_count FROM admissions;
SELECT 'labevents' AS table_name, COUNT(*) AS row_count FROM labevents;

-- 3) Missingness: always state both numerator and denominator.
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN valuenum IS NULL THEN 1 ELSE 0 END) AS missing_valuenum,
    ROUND(
        100.0 * SUM(CASE WHEN valuenum IS NULL THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS missing_percent
FROM labevents;

-- 4) Availability lag: the result time is not necessarily the measurement time.
SELECT
    charttime,
    storetime,
    ROUND(
        (julianday(storetime) - julianday(charttime)) * 24.0 * 60.0,
        2
    ) AS availability_lag_minutes
FROM labevents
WHERE charttime IS NOT NULL
  AND storetime IS NOT NULL
LIMIT 20;
