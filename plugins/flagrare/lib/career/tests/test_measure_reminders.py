from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import measure_reminders as mr  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
CONFIG = ".claude/skills/flagrare/config.json"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def measurement(**over) -> dict:
    base = {"id": "acme-reorder", "work": {"title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket"},
            "stage": "before", "launch_date": "2026-10-01",
            "checks": [{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14}],
            "created_at": "2026-09-20", "updated_at": "2026-10-01"}
    base.update(over)
    return base


class SessionStart(unittest.TestCase):
    def test_given_nothing_saved_when_a_session_starts_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(mr.session_start(d, "2026-10-16"))

    def test_given_a_check_due_when_a_session_starts_then_shows_one_line_and_tells_claude_the_details(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([measurement()]))
            out = mr.session_start(d, "2026-10-16")
            self.assertEqual(out["systemMessage"], "Impact: 1 check due (Reorder button for Acme Pizza). Ask Claude to measure it when you have a minute.")
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertIn("acme-reorder", out["hookSpecificOutput"]["additionalContext"])

    def test_given_checks_and_recent_wins_due_when_a_session_starts_then_counts_each_kind(self):
        with tempfile.TemporaryDirectory() as d:
            two = measurement(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14},
                                      {"due": "2026-10-16", "done_at": None, "value": None, "verdict": None, "after_days": 42}])
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([two]))
            write(Path(d), f"{CAREER}/contributions.log.md", "- 2026-10-10 | https://chat.example/p1 | Helped Sam | behavior: x\n")
            out = mr.session_start(d, "2026-10-16")
            self.assertEqual(out["systemMessage"], "Impact: 2 checks due (Reorder button for Acme Pizza, and more), 1 recent win with no number. Ask Claude to measure them when you have a minute.")

    def test_given_reminders_turned_off_when_a_session_starts_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([measurement()]))
            write(Path(d), CONFIG, json.dumps({"skills": {"measure-impact": {"reminders": False}}}))
            self.assertIsNone(mr.session_start(d, "2026-10-16"))

    def test_given_a_corrupt_file_when_a_session_starts_then_names_the_file_in_one_line(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{oops")
            out = mr.session_start(d, "2026-10-16")
            self.assertIn("measurements.json", out["systemMessage"])
            self.assertNotIn("Traceback", out["systemMessage"])


if __name__ == "__main__":
    unittest.main()
