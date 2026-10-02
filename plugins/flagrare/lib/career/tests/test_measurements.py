from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import measurements as m  # noqa: E402

CAREER = ".claude/skills/flagrare/career"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def entry(**over) -> dict:
    base = {
        "id": "acme-reorder",
        "work": {"title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket"},
        "stage": "before",
        "metric": {"name": "repeat orders per week", "why": "the button exists to bring people back"},
        "source": {"category": "data warehouse", "tool": "warehouse", "query": "select count(*) from orders", "run_at": "2026-10-01"},
        "baseline": {"value": "120 a week", "as_of": "2026-10-01", "confidence": "direct"},
        "bet": {"sentence": "We believe a reorder button will lift repeat orders, because Kai's survey says people retype orders", "range": "130 to 160 a week", "confidence": "inferred"},
        "ownership": "mine",
    }
    base.update(over)
    return base


class Load(unittest.TestCase):
    def test_given_no_file_when_loading_then_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.load(d), [])

    def test_given_a_valid_file_when_loading_then_returns_its_entries(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([entry()]))
            self.assertEqual(m.load(d)[0]["id"], "acme-reorder")

    def test_given_a_corrupt_file_when_loading_then_refuses_instead_of_returning_empty(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{not json")
            with self.assertRaises(m.CorruptFile):
                m.load(d)

    def test_given_a_file_that_is_not_a_list_when_loading_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "{}")
            with self.assertRaises(m.CorruptFile):
                m.load(d)


class CheckEntry(unittest.TestCase):
    def test_given_a_complete_entry_when_checking_then_accepts_it(self):
        m.check_entry(entry())

    def test_given_an_unknown_stage_when_checking_then_names_the_allowed_stages(self):
        with self.assertRaisesRegex(ValueError, "stage must be one of"):
            m.check_entry(entry(stage="during"))

    def test_given_an_unknown_confidence_level_when_checking_then_refuses(self):
        bad = entry(baseline={"value": "120", "as_of": "2026-10-01", "confidence": "pretty sure"})
        with self.assertRaisesRegex(ValueError, "baseline confidence must be one of"):
            m.check_entry(bad)

    def test_given_an_unknown_ownership_when_checking_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "ownership must be one of"):
            m.check_entry(entry(ownership="everyone"))

    def test_given_work_without_a_title_when_checking_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "work needs a title"):
            m.check_entry(entry(work={"title": "", "link": "x", "kind": "ticket"}))

    def test_given_a_badly_formatted_date_when_checking_then_refuses(self):
        bad = entry(baseline={"value": "120", "as_of": "Oct 1", "confidence": "direct"})
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            m.check_entry(bad)


if __name__ == "__main__":
    unittest.main()
