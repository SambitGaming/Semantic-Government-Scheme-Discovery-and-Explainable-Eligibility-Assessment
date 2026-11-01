import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.automation.scheme_extractor import extract_scheme
from src.automation.scheme_validator import validate_scheme
from src.automation.duplicate_detector import find_duplicate, normalize_name


class AutomationTests(unittest.TestCase):
    def sample_page(self):
        return {
            "title": "Example Scholarship",
            "description": "Scholarship support for eligible students.",
            "url": "https://example.gov.in/scholarship",
            "sections": [
                {"heading": "Eligibility Criteria", "text": "Applicants must meet the published criteria."},
                {"heading": "Benefits", "text": "Financial assistance is provided to eligible students."},
                {"heading": "Required Documents", "text": "Income certificate and student ID."},
            ],
        }

    def test_extracts_eligibility_heading(self):
        record = extract_scheme(self.sample_page())
        self.assertEqual(record["scheme_name_candidate"], "Example Scholarship")
        self.assertEqual(len(record["eligibility_candidates"]), 1)

    def test_validator_flags_missing_eligibility(self):
        record = extract_scheme({
            "title": "Example Scholarship",
            "description": "A test description",
            "url": "https://example.gov.in/scholarship",
            "sections": [{"heading": "Benefits", "text": "Financial assistance"}],
        })
        record = validate_scheme(record)
        self.assertIn("Eligibility section not detected", record["validation_issues"])
        self.assertEqual(record["verification_status"], "pending_review")

    def test_validator_accepts_basic_complete_candidate(self):
        record = validate_scheme(extract_scheme(self.sample_page()))
        self.assertEqual(record["validation_status"], "ready_for_review")
        self.assertEqual(record["verification_status"], "pending_review")

    def test_duplicate_detection_by_name(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            saved = {
                "scheme_name_candidate": "Example Scholarship",
                "official_url": "https://different.gov.in/other",
            }
            (folder / "saved.json").write_text(json.dumps(saved), encoding="utf-8")
            candidate = {
                "scheme_name_candidate": "Example Scholarship",
                "official_url": "https://example.gov.in/scholarship",
            }
            self.assertIsNotNone(find_duplicate(candidate, [folder], "current"))
            self.assertEqual(normalize_name("Example-Scholarship!"), "example scholarship")


if __name__ == "__main__":
    unittest.main()
