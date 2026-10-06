import copy
import unittest

from fhirlab import mapping as m
from fhirlab.generate import generate
from fhirlab.transform import build_bundle, clean_value, fhir_datetime
from fhirlab.validate import validate_bundle

PATIENT = {"mrn": "SYN-0001", "first_name": "Lina", "last_name": "Haddad", "sex": "F",
           "birth_date": "1980-05-17"}


def obs(code, value, unit, when="2025-03-01 09:30", mrn="SYN-0001"):
    return {"mrn": mrn, "taken_at": when, "code": code, "value": value, "unit": unit}


def resources(bundle, kind):
    return [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == kind]


class CleaningTests(unittest.TestCase):
    def test_glucose_mmol_converted_to_mg_dl(self):
        code, value = clean_value(obs("GLU", "5.5", "mmol/L"))
        self.assertEqual(code, "GLU")
        self.assertAlmostEqual(value, 99.088)

    def test_rejections_have_reasons(self):
        cases = [(obs("HR", "abc", "bpm"), "not a number"),
                 (obs("TEMP", 45, "C"), "outside plausible range"),
                 (obs("XYZ", 1, "x"), "unknown local code"),
                 (obs("GLU", 5, "g/L"), "not accepted")]
        for row, reason in cases:
            with self.subTest(row=row["code"]), self.assertRaisesRegex(ValueError, reason):
                clean_value(row)

    def test_datetime_has_time_zone(self):
        self.assertEqual(fhir_datetime("2025-03-01 09:30"), "2025-03-01T09:30:00Z")


class TransformTests(unittest.TestCase):
    def test_patient_mapping(self):
        bundle, _ = build_bundle([PATIENT], [])
        p = resources(bundle, "Patient")[0]
        self.assertEqual(p["gender"], "female")
        self.assertEqual(p["identifier"][0], {"system": m.MRN_SYSTEM, "value": "SYN-0001"})
        self.assertEqual(p["meta"]["security"][0]["code"], "HTEST")
        self.assertEqual(bundle["entry"][0]["request"]["method"], "PUT")

    def test_heart_rate_uses_loinc_and_ucum(self):
        bundle, rejected = build_bundle([PATIENT], [obs("HR", 72, "bpm")])
        self.assertEqual(rejected, [])
        o = resources(bundle, "Observation")[0]
        self.assertEqual(o["code"]["coding"][0]["code"], "8867-4")
        self.assertEqual(o["valueQuantity"]["code"], "/min")
        self.assertEqual(o["category"][0]["coding"][0]["code"], "vital-signs")
        self.assertEqual(o["subject"]["reference"], bundle["entry"][0]["fullUrl"])

    def test_blood_pressure_becomes_one_panel(self):
        bundle, rejected = build_bundle([PATIENT], [obs("SBP", 120, "mmHg"), obs("DBP", 80, "mmHg")])
        self.assertEqual(rejected, [])
        observations = resources(bundle, "Observation")
        self.assertEqual(len(observations), 1)
        panel = observations[0]
        self.assertEqual(panel["code"]["coding"][0]["code"], "85354-9")
        self.assertEqual([c["code"]["coding"][0]["code"] for c in panel["component"]], ["8480-6", "8462-4"])

    def test_half_blood_pressure_rejected(self):
        _, rejected = build_bundle([PATIENT], [obs("SBP", 120, "mmHg")])
        self.assertIn("both systolic and diastolic", rejected[0]["reason"])

    def test_unknown_patient_rejected(self):
        _, rejected = build_bundle([PATIENT], [obs("HR", 80, "bpm", mrn="SYN-9999")])
        self.assertIn("not found", rejected[0]["reason"])

    def test_output_is_repeatable(self):
        rows = [obs("HR", 72, "bpm")]
        self.assertEqual(build_bundle([PATIENT], rows), build_bundle([PATIENT], rows))


class EndToEndTests(unittest.TestCase):
    def test_generated_export_transforms_and_validates(self):
        patients, observations = generate(n_patients=10, seed=1)
        bundle, rejected = build_bundle(patients, observations)
        self.assertEqual(validate_bundle(bundle), [])
        self.assertEqual(len(resources(bundle, "Patient")), 10)
        # exactly the 5 deliberately broken rows are rejected
        self.assertEqual(len(rejected), 5)

    def test_validator_catches_broken_reference(self):
        bundle, _ = build_bundle([PATIENT], [obs("HR", 72, "bpm")])
        broken = copy.deepcopy(bundle)
        resources(broken, "Observation")[0]["subject"]["reference"] = "urn:uuid:missing"
        self.assertTrue(any("subject" in p for p in validate_bundle(broken)))


if __name__ == "__main__":
    unittest.main()
