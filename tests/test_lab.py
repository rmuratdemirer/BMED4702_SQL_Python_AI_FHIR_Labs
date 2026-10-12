from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path

from src.ai_explain import assert_numeric_grounding, deterministic_explanation


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "mimic_demo.sqlite"


def connection() -> sqlite3.Connection:
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    return con


class LabTests(unittest.TestCase):
    def test_expected_table_counts(self) -> None:
        expected = {"patients": 100, "admissions": 275, "d_labitems": 1622, "labevents": 107727}
        with connection() as con:
            observed = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in expected}
        self.assertEqual(observed, expected)

    def test_creatinine_example_has_event_grain(self) -> None:
        sql = (ROOT / "sql" / "02_creatinine_timeline.sql").read_text(encoding="utf-8")
        params = {"subject_id": 10035631, "hadm_id": 29276678, "itemid": 50912}
        with connection() as con:
            rows = con.execute(sql, params).fetchall()
        self.assertEqual(len(rows), 36)
        self.assertEqual(len({row[0] for row in rows}), 36)
        self.assertEqual(min(row["valuenum"] for row in rows), 1.0)
        self.assertEqual(max(row["valuenum"] for row in rows), 5.3)

    def test_wrong_join_is_visibly_inflated(self) -> None:
        with connection() as con:
            wrong = con.execute(
                "SELECT COUNT(*) FROM admissions a JOIN labevents l ON a.subject_id=l.subject_id"
            ).fetchone()[0]
            correct = con.execute(
                "SELECT COUNT(*) FROM admissions a JOIN labevents l "
                "ON a.subject_id=l.subject_id AND a.hadm_id=l.hadm_id"
            ).fetchone()[0]
        self.assertEqual(wrong, 732303)
        self.assertEqual(correct, 79307)
        self.assertGreater(wrong / correct, 9)

    def test_deterministic_ai_text_uses_grounded_numbers(self) -> None:
        evidence = json.loads((ROOT / "output" / "evidence_summary.json").read_text(encoding="utf-8"))
        text = deterministic_explanation(evidence)
        assert_numeric_grounding(text, evidence)


if __name__ == "__main__":
    unittest.main()
