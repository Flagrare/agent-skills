from __future__ import annotations
import sys
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


class Conflicts(unittest.TestCase):
    def test_given_two_sources_disagree_when_listing_conflicts_then_both_kept_and_path_reported(self):
        fact = {
            "status": "unverified",
            "alternatives": [
                {"value": "Neil", "source": "notion", "checked_at": "2026-09-30", "status": "unverified"},
                {"value": "Karen", "source": "miro", "checked_at": "2026-09-30", "status": "unverified"},
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


if __name__ == "__main__":
    unittest.main()
