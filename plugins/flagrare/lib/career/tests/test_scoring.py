from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scoring  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
FACT = {"value": "x", "source": "https://example.com", "checked_at": "2026-09-30", "status": "verified"}
MAP = {
    "rubric": {"rows": [
        {"id": "scope.proactive-discovery", "area": "Scope & Impact", "status": "partial",
         "target_text": {**FACT, "value": "Proactively discovers and solves problems"}},
        {"id": "craft.code-quality", "area": "Technical Craft", "status": "done", "target_text": FACT},
    ]},
    "people": [
        {"name": "Sam Rivera", "seen_your_work": True},
        {"name": "Alex Chen", "seen_your_work": False},
    ],
}


def write(home: Path, rel: str, data: object) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data))


class OpenRows(unittest.TestCase):
    def test_given_rows_when_listing_then_only_not_done_rows_with_plain_target_text(self):
        self.assertEqual(scoring.open_rows(MAP), [
            {"id": "scope.proactive-discovery", "area": "Scope & Impact", "target_text": "Proactively discovers and solves problems"}])

    def test_given_map_without_rubric_when_listing_then_empty(self):
        self.assertEqual(scoring.open_rows({"target": {}}), [])


class UnseenPeople(unittest.TestCase):
    def test_given_people_when_listing_then_only_those_who_have_not_seen_the_work(self):
        self.assertEqual(scoring.unseen_people(MAP), ["Alex Chen"])


class Context(unittest.TestCase):
    def test_given_no_map_when_building_context_then_fallback_from_legacy_config(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, ".claude/skills/flagrare/config.json", {"skills": {"senior-scan": {"target_behaviors": ["unblocking others"], "audience": ["a manager"]}}})
            ctx = scoring.context(str(home))
            self.assertFalse(ctx["has_map"])
            self.assertEqual(ctx["fallback"], {"target_behaviors": ["unblocking others"], "audience": ["a manager"]})

    def test_given_map_when_building_context_then_lists_open_rows_and_unseen_people(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", MAP)
            ctx = scoring.context(str(home))
            self.assertTrue(ctx["has_map"])
            self.assertEqual([r["id"] for r in ctx["open_rows"]], ["scope.proactive-discovery"])
            self.assertEqual(ctx["unseen_people"], ["Alex Chen"])


if __name__ == "__main__":
    unittest.main()
