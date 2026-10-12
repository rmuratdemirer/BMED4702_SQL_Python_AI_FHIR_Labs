from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_COLUMNS: dict[str, set[str]] = {
    "patients": {"subject_id", "gender", "anchor_age", "anchor_year", "anchor_year_group"},
    "admissions": {
        "subject_id", "hadm_id", "admittime", "dischtime", "admission_type",
        "admission_location", "discharge_location", "hospital_expire_flag",
    },
    "d_labitems": {"itemid", "label", "fluid", "category"},
    "labevents": {
        "labevent_id", "subject_id", "hadm_id", "specimen_id", "itemid",
        "charttime", "storetime", "value", "valuenum", "valueuom",
        "ref_range_lower", "ref_range_upper", "flag", "priority",
    },
}

ALLOWED_FUNCTIONS = {
    "avg", "coalesce", "count", "date", "datetime", "julianday", "max",
    "min", "round", "strftime", "sum", "total",
}

DANGEROUS_KEYWORDS = re.compile(
    r"\b(attach|detach|alter|analyze|create|delete|drop|insert|pragma|reindex|"
    r"replace|savepoint|transaction|trigger|update|vacuum|virtual)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class CandidateQuery:
    sql: str
    params: dict[str, Any]
    generator: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def deterministic_candidate(question: str) -> CandidateQuery:
    q = " ".join(question.lower().split())
    if "how many" in q and "patient" in q:
        return CandidateQuery(
            "SELECT COUNT(DISTINCT subject_id) AS patient_count FROM patients",
            {}, "deterministic-template",
        )
    if "how many" in q and ("admission" in q or "encounter" in q):
        return CandidateQuery(
            "SELECT COUNT(DISTINCT hadm_id) AS admission_count FROM admissions",
            {}, "deterministic-template",
        )
    if "missing" in q and "hadm" in q:
        return CandidateQuery(
            "SELECT COUNT(*) AS missing_hadm_id FROM labevents WHERE hadm_id IS NULL",
            {}, "deterministic-template",
        )
    if "mean" in q or "average" in q:
        if "lag" in q or "availability" in q:
            return CandidateQuery(
                """SELECT ROUND(AVG((julianday(storetime)-julianday(charttime))*1440.0), 2)
                          AS mean_availability_minutes
                   FROM labevents
                   WHERE itemid = :itemid AND storetime IS NOT NULL""",
                {"itemid": 50912}, "deterministic-template",
            )
    if "creatinine" in q and ("timeline" in q or "series" in q):
        subject = re.search(r"subject\D+(\d+)", q)
        admission = re.search(r"(?:admission|hadm)\D+(\d+)", q)
        if not subject or not admission:
            raise ValueError("The creatinine timeline question must include subject and admission IDs")
        return CandidateQuery(
            """SELECT l.labevent_id, l.charttime, l.storetime, l.valuenum, l.valueuom,
                          l.ref_range_lower, l.ref_range_upper, l.flag
                   FROM labevents AS l
                   JOIN d_labitems AS d ON d.itemid = l.itemid
                   WHERE l.subject_id = :subject_id
                     AND l.hadm_id = :hadm_id
                     AND l.itemid = :itemid
                     AND l.valuenum IS NOT NULL
                   ORDER BY l.charttime, l.labevent_id""",
            {
                "subject_id": int(subject.group(1)),
                "hadm_id": int(admission.group(1)),
                "itemid": 50912,
            },
            "deterministic-template",
        )
    raise ValueError(
        "Question is outside the deterministic teaching intents. Try patient/admission counts, "
        "missing hadm_id, mean availability lag, or a creatinine timeline with IDs."
    )


def model_candidate(question: str) -> CandidateQuery:
    if os.getenv("AI_SQL_ENABLED", "false").lower() != "true":
        return deterministic_candidate(question)
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not model:
        raise RuntimeError("Set OPENAI_MODEL when AI_SQL_ENABLED=true")
    from openai import OpenAI

    schema = {table: sorted(columns) for table, columns in ALLOWED_COLUMNS.items()}
    instructions = (
        "Return one JSON object with keys sql and params. Generate exactly one read-only SQLite "
        "SELECT or WITH...SELECT query. Use only the supplied schema, named parameters, and these "
        "functions: " + ", ".join(sorted(ALLOWED_FUNCTIONS)) + ". Never use comments, PRAGMA, "
        "DDL, DML, ATTACH, sqlite_master, or multiple statements. If the question is not answerable, "
        "return {\"sql\":\"\",\"params\":{},\"reason\":\"not answerable\"}."
    )
    payload = {"schema": schema, "question": question}
    response = OpenAI().responses.create(
        model=model,
        instructions=instructions,
        input=json.dumps(payload),
    )
    raw = response.output_text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.DOTALL)
    data = json.loads(raw)
    if not data.get("sql"):
        raise ValueError(data.get("reason", "Model declined the question"))
    params = data.get("params", {})
    if not isinstance(params, dict):
        raise ValueError("Model params must be a JSON object")
    return CandidateQuery(str(data["sql"]), params, f"model:{model}")


def validate_sql(sql: str, params: dict[str, Any]) -> str:
    candidate = sql.strip()
    if candidate.endswith(";"):
        candidate = candidate[:-1].rstrip()
    if not candidate:
        raise ValueError("Empty SQL")
    if ";" in candidate:
        raise ValueError("Multiple statements are not allowed")
    if "--" in candidate or "/*" in candidate or "*/" in candidate:
        raise ValueError("SQL comments are not allowed")
    if not re.match(r"^(select|with)\b", candidate, flags=re.IGNORECASE):
        raise ValueError("Only SELECT or WITH...SELECT is allowed")
    if DANGEROUS_KEYWORDS.search(candidate):
        raise ValueError("A forbidden SQL keyword was detected")
    for key, value in params.items():
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"Invalid parameter name: {key}")
        if not isinstance(value, (str, int, float, type(None))):
            raise ValueError(f"Unsupported parameter type for {key}")
    return candidate


def _authorizer(action: int, arg1: str | None, arg2: str | None, _db: str | None, _source: str | None) -> int:
    if action in {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE}:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION:
        function_name = (arg2 or arg1 or "").lower()
        return sqlite3.SQLITE_OK if function_name in ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_READ:
        table = (arg1 or "").lower()
        column = (arg2 or "").lower()
        if table in ALLOWED_COLUMNS and (column in ALLOWED_COLUMNS[table] or column == ""):
            return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def execute_safe(
    database: Path,
    candidate: CandidateQuery,
    max_rows: int = 100,
    timeout_seconds: float = 2.0,
) -> tuple[str, list[dict[str, Any]]]:
    sql = validate_sql(candidate.sql, candidate.params)
    if not 1 <= max_rows <= 500:
        raise ValueError("max_rows must be between 1 and 500")
    uri = database.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA query_only=ON")
        deadline = time.monotonic() + timeout_seconds
        con.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
        con.set_authorizer(_authorizer)
        wrapped = f"SELECT * FROM ({sql}) AS safe_result LIMIT :__safe_limit"
        parameters = dict(candidate.params)
        parameters["__safe_limit"] = max_rows
        rows = [dict(row) for row in con.execute(wrapped, parameters).fetchall()]
    finally:
        con.close()
    return sql, rows


def run_question(
    question: str,
    database: Path,
    output_dir: Path,
    max_rows: int = 100,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit: dict[str, Any] = {
        "question": question,
        "started_at": _utc_now(),
        "database": database.name,
        "policy": {
            "read_only_uri": True,
            "query_only": True,
            "authorizer_default": "deny",
            "allowed_tables": sorted(ALLOWED_COLUMNS),
            "max_rows": max_rows,
            "timeout_seconds": 2.0,
        },
    }
    try:
        candidate = model_candidate(question)
        audit["generator"] = candidate.generator
        audit["candidate_sql_sha256"] = _sha256_text(candidate.sql)
        sql, rows = execute_safe(database, candidate, max_rows=max_rows)
        audit.update({
            "status": "executed",
            "validated_sql": sql,
            "parameters": candidate.params,
            "row_count": len(rows),
            "finished_at": _utc_now(),
        })
        result_path = output_dir / "nl_sql_result.csv"
        with result_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["no_rows"])
            writer.writeheader()
            if rows:
                writer.writerows(rows)
        audit["result_file"] = result_path.name
    except Exception as exc:
        audit.update({"status": "rejected", "reason": str(exc), "finished_at": _utc_now()})
        rows = []
    (output_dir / "query_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return {"audit": audit, "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely translate a teaching question to read-only SQL")
    parser.add_argument("question")
    parser.add_argument("--database", type=Path, default=Path("data/mimic_demo.sqlite"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--max-rows", type=int, default=100)
    args = parser.parse_args()
    result = run_question(args.question, args.database, args.output_dir, args.max_rows)
    print(json.dumps(result, indent=2, default=str))
    if result["audit"]["status"] != "executed":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
