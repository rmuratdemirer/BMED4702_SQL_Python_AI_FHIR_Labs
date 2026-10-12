from __future__ import annotations

import unittest
from pathlib import Path

from src.fhir_observation import build_bundle, validate_bundle


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "mimic_demo.sqlite"


class FhirObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = build_bundle(DB, ROOT, "+00:00")
        cls.observations = [
            entry["resource"] for entry in cls.bundle["entry"]
            if entry["resource"]["resourceType"] == "Observation"
        ]

    def test_one_observation_per_lab_event(self) -> None:
        self.assertEqual(len(self.observations), 36)
        self.assertEqual(len({obs["id"] for obs in self.observations}), 36)

    def test_first_observation_has_required_mapping(self) -> None:
        obs = self.observations[0]
        self.assertEqual(obs["status"], "unknown")
        self.assertEqual(obs["valueQuantity"]["system"], "http://unitsofmeasure.org")
        self.assertEqual(obs["valueQuantity"]["code"], "mg/dL")
        self.assertTrue(any(c["code"] == "38483-4" for c in obs["code"]["coding"]))
        self.assertTrue(obs["effectiveDateTime"].endswith("+00:00"))

    def test_bundle_contract_validates(self) -> None:
        report = validate_bundle(self.bundle, 36)
        self.assertTrue(report["valid_for_lab_contract"], report["errors"])

    def test_provenance_targets_all_observations(self) -> None:
        provenance = next(
            entry["resource"] for entry in self.bundle["entry"]
            if entry["resource"]["resourceType"] == "Provenance"
        )
        self.assertEqual(len(provenance["target"]), 36)


if __name__ == "__main__":
    unittest.main()
