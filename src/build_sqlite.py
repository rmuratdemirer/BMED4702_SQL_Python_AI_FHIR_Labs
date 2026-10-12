from __future__ import annotations

import argparse
import csv
import gzip
import sqlite3
from collections.abc import Iterable
from pathlib import Path


SCHEMAS: dict[str, tuple[str, tuple[str, ...]]] = {
    "patients": (
        """CREATE TABLE patients (
            subject_id INTEGER PRIMARY KEY,
            gender TEXT,
            anchor_age INTEGER,
            anchor_year INTEGER,
            anchor_year_group TEXT,
            dod TEXT
        )""",
        ("subject_id", "gender", "anchor_age", "anchor_year", "anchor_year_group", "dod"),
    ),
    "admissions": (
        """CREATE TABLE admissions (
            subject_id INTEGER NOT NULL,
            hadm_id INTEGER PRIMARY KEY,
            admittime TEXT,
            dischtime TEXT,
            admission_type TEXT,
            race TEXT,
            hospital_expire_flag INTEGER
        )""",
        ("subject_id", "hadm_id", "admittime", "dischtime", "admission_type", "race", "hospital_expire_flag"),
    ),
    "d_labitems": (
        """CREATE TABLE d_labitems (
            itemid INTEGER PRIMARY KEY,
            label TEXT,
            fluid TEXT,
            category TEXT
        )""",
        ("itemid", "label", "fluid", "category"),
    ),
    "labevents": (
        """CREATE TABLE labevents (
            labevent_id INTEGER PRIMARY KEY,
            subject_id INTEGER NOT NULL,
            hadm_id INTEGER,
            specimen_id INTEGER,
            itemid INTEGER NOT NULL,
            charttime TEXT,
            storetime TEXT,
            value TEXT,
            valuenum REAL,
            valueuom TEXT,
            ref_range_lower REAL,
            ref_range_upper REAL,
            flag TEXT,
            priority TEXT
        )""",
        (
            "labevent_id", "subject_id", "hadm_id", "specimen_id", "itemid",
            "charttime", "storetime", "value", "valuenum", "valueuom",
            "ref_range_lower", "ref_range_upper", "flag", "priority",
        ),
    ),
}

INTEGER_COLUMNS = {
    "subject_id", "hadm_id", "labevent_id", "specimen_id", "itemid",
    "anchor_age", "anchor_year", "hospital_expire_flag",
}
REAL_COLUMNS = {"valuenum", "ref_range_lower", "ref_range_upper"}


def convert(field: str, value: str) -> object:
    if value == "":
        return None
    if field in INTEGER_COLUMNS:
        return int(value)
    if field in REAL_COLUMNS:
        return float(value)
    return value


def batched(rows: Iterable[tuple[object, ...]], size: int = 5000) -> Iterable[list[tuple[object, ...]]]:
    batch: list[tuple[object, ...]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def selected_rows(path: Path, columns: tuple[str, ...]) -> Iterable[tuple[object, ...]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        for record in csv.DictReader(stream):
            yield tuple(convert(column, record[column]) for column in columns)


def build(source_root: Path, output: Path) -> None:
    hosp = source_root / "hosp"
    required = {table: hosp / f"{table}.csv.gz" for table in SCHEMAS}
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing official Demo files:\n" + "\n".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(output) as con:
        con.execute("PRAGMA journal_mode = WAL")
        for table, (ddl, columns) in SCHEMAS.items():
            con.execute(f"DROP TABLE IF EXISTS {table}")
            con.execute(ddl)
            placeholders = ",".join("?" for _ in columns)
            column_list = ",".join(columns)
            insert_sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
            for batch in batched(selected_rows(required[table], columns)):
                con.executemany(insert_sql, batch)
            con.commit()

        con.execute("CREATE INDEX idx_admissions_subject ON admissions(subject_id)")
        con.execute("CREATE INDEX idx_labs_subject_admission ON labevents(subject_id, hadm_id)")
        con.execute("CREATE INDEX idx_labs_item_time ON labevents(itemid, charttime)")
        con.commit()

        expected = {"patients": 100, "admissions": 275, "d_labitems": 1622, "labevents": 107727}
        observed = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in expected}
        if observed != expected:
            raise RuntimeError(f"Row-count verification failed: {observed}")
        print("Verified row counts:", observed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", type=Path, help="Extracted mimic-iv-clinical-database-demo-2.2 folder")
    parser.add_argument("--output", type=Path, default=Path("data/mimic_demo.sqlite"))
    args = parser.parse_args()
    build(args.source_root, args.output)


if __name__ == "__main__":
    main()
