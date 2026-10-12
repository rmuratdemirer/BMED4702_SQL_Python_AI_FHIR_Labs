from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.safe_nl_sql import CandidateQuery, execute_safe, run_question


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "mimic_demo.sqlite"


class SafeNaturalLanguageSqlTests(unittest.TestCase):
    def test_approved_count_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_question("How many admissions are in the demo?", DB, Path(tmp))
        self.assertEqual(result["audit"]["status"], "executed")
        self.assertEqual(result["rows"][0]["admission_count"], 275)

    def test_mutation_is_rejected(self) -> None:
        candidate = CandidateQuery("DELETE FROM admissions", {}, "test")
        with self.assertRaises(ValueError):
            execute_safe(DB, candidate)

    def test_unauthorized_column_is_rejected(self) -> None:
        candidate = CandidateQuery("SELECT insurance FROM admissions", {}, "test")
        with self.assertRaises(Exception):
            execute_safe(DB, candidate)

    def test_multiple_statements_are_rejected(self) -> None:
        candidate = CandidateQuery("SELECT 1; SELECT 2", {}, "test")
        with self.assertRaises(ValueError):
            execute_safe(DB, candidate)


if __name__ == "__main__":
    unittest.main()
