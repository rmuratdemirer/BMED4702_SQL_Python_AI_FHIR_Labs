import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_week2_visual_demo import SAMPLE_ROW, to_fhir_observation, validate


class MappingContractTests(unittest.TestCase):
    def test_null_hadm_does_not_create_encounter(self):
        resource, _ = to_fhir_observation(dict(SAMPLE_ROW, hadm_id=None))
        self.assertNotIn("encounter", resource)

    def test_known_unit_gets_ucum(self):
        resource, _ = to_fhir_observation(dict(SAMPLE_ROW, valueuom="mg/dL"))
        quantity = resource["valueQuantity"]
        self.assertEqual(quantity["system"], "http://unitsofmeasure.org")
        self.assertEqual(quantity["code"], "mg/dL")

    def test_unknown_unit_is_preserved_not_asserted(self):
        resource, warnings = to_fhir_observation(dict(SAMPLE_ROW, valueuom="mystery"))
        quantity = resource["valueQuantity"]
        self.assertEqual(quantity["unit"], "mystery")
        self.assertNotIn("system", quantity)
        self.assertTrue(warnings)

    def test_safe_mapping_has_no_errors(self):
        resource, _ = to_fhir_observation(SAMPLE_ROW)
        issues = validate(resource, SAMPLE_ROW)
        self.assertFalse([x for x in issues if x["severity"] == "error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
