from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import map_schema as ms  # noqa: E402

GOOD_FACT = {"value": "Senior", "source": "https://x", "checked_at": "2026-09-30", "status": "verified"}


class Validate(unittest.TestCase):
    def test_given_partial_map_after_phase_two_when_validating_then_no_errors_and_rest_missing(self):
        m = {
            "target": {"target_level": GOOD_FACT},
            "rubric": {"rows": []},
            "sections": {"target": {"checked_at": "2026-09-30"}, "rubric": {"checked_at": "2026-09-30"}},
        }
        self.assertEqual(ms.validate(m), [])
        self.assertIn("org", ms.missing_sections(m))
        self.assertNotIn("target", ms.missing_sections(m))

    def test_given_fact_without_source_when_validating_then_reports_its_path(self):
        m = {"target": {"target_level": {"value": "Senior", "checked_at": "2026-09-30", "status": "verified"}}}
        errors = ms.validate(m)
        self.assertTrue(any("target.target_level" in e and "source" in e for e in errors))

    def test_given_unknown_status_when_validating_then_reports_it(self):
        m = {"target": {"target_level": {**GOOD_FACT, "status": "probably"}}}
        self.assertTrue(any("status" in e for e in ms.validate(m)))


class Priorities(unittest.TestCase):
    def test_given_priorities_with_a_fact_missing_its_status_when_validating_then_reports_it(self):
        m = {"priorities": [{"theme": "Merchant trust", "metric": {"value": "merchant satisfaction score", "source": "https://x", "checked_at": "2026-09-30"}}]}
        self.assertEqual(ms.validate(m), ["priorities[0].metric: missing status"])

    def test_given_priorities_checked_long_ago_when_listing_stale_sections_then_reports_them(self):
        m = {"priorities": [], "sections": {"priorities": {"checked_at": "2026-01-01"}}}
        self.assertIn("priorities", ms.stale_sections(m, date(2026, 10, 1)))

    def test_given_no_priorities_when_listing_missing_sections_then_it_is_not_required(self):
        self.assertNotIn("priorities", ms.missing_sections({}))


class Conflicts(unittest.TestCase):
    def test_given_two_sources_disagree_when_listing_conflicts_then_both_kept_and_path_reported(self):
        fact = {
            "status": "unverified",
            "alternatives": [
                {"value": "Alex", "source": "notion", "checked_at": "2026-09-30", "status": "unverified"},
                {"value": "Sam", "source": "miro", "checked_at": "2026-09-30", "status": "unverified"},
            ],
        }
        m = {"org": {"n2_manager_reports_to": fact}}
        self.assertEqual(ms.validate(m), [])
        self.assertEqual(ms.conflicts(m), ["org.n2_manager_reports_to"])


class Stale(unittest.TestCase):
    def test_given_section_checked_over_90_days_ago_when_checking_then_stale(self):
        m = {"org": {}, "sections": {"org": {"checked_at": "2026-05-01"}}}
        self.assertEqual(ms.stale_sections(m, date(2026, 9, 30)), ["org"])

    def test_given_present_section_without_checked_at_when_checking_then_stale(self):
        self.assertEqual(ms.stale_sections({"people": []}, date(2026, 9, 30)), ["people"])

    def test_given_absent_section_when_checking_then_not_stale(self):
        self.assertEqual(ms.stale_sections({}, date(2026, 9, 30)), [])


class RubricRow(unittest.TestCase):
    def test_given_rubric_row_with_status_when_validating_then_no_errors(self):
        row = {
            "id": "scope.x",
            "status": "partial",
            "current_text": GOOD_FACT,
            "target_text": GOOD_FACT,
            "evidence": [],
        }
        m = {"rubric": {"rows": [row]}}
        self.assertEqual(ms.validate(m), [])


class MissingStatus(unittest.TestCase):
    def test_given_fact_without_status_when_validating_then_reports_missing_status(self):
        m = {"target": {"target_level": {"value": "Senior", "source": "https://x", "checked_at": "2026-09-30"}}}
        errors = ms.validate(m)
        self.assertTrue(any("target.target_level" in e and "status" in e for e in errors))


class BadDate(unittest.TestCase):
    def test_given_fact_with_invalid_checked_at_when_validating_then_reports_error(self):
        m = {"target": {"target_level": {**GOOD_FACT, "checked_at": "soon"}}}
        errors = ms.validate(m)
        self.assertTrue(any("checked_at" in e and "ISO date" in e for e in errors))


class StaleWithBadDate(unittest.TestCase):
    def test_given_stale_sections_with_malformed_date_when_checking_then_returns_stale_without_exception(self):
        m = {"org": {}, "sections": {"org": {"checked_at": "not-a-date"}}}
        result = ms.stale_sections(m, date(2026, 9, 30))
        self.assertEqual(result, ["org"])


class Cli(unittest.TestCase):
    def test_given_valid_map_file_when_running_cli_then_outputs_json_with_required_keys(self):
        valid_map = {
            "target": {"target_level": GOOD_FACT},
            "sections": {"target": {"checked_at": "2026-09-30"}},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(valid_map, f)
            temp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parents[1] / "map_schema.py"),
                 "check", temp_path, "--today", "2026-09-30"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            self.assertIn("errors", output)
            self.assertIn("missing", output)
            self.assertIn("stale", output)
            self.assertIn("conflicts", output)
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    unittest.main()
