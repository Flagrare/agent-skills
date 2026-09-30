from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BOARD = Path(__file__).resolve().parents[1] / "board"
sys.path.insert(0, str(BOARD))
import build  # noqa: E402

LEGACY = ".claude/skills/flagrare/senior-scan"
CAREER = ".claude/skills/flagrare/career"


class ParseContributions(unittest.TestCase):
    def test_given_old_free_text_entry_when_parsing_then_keeps_behavior_and_no_row(self):
        [c] = build.parse_contributions(["- 2026-09-30 | https://x | fixed a thing | behavior: unblocking others"])
        self.assertEqual(c["behavior"], "unblocking others")
        self.assertIsNone(c["row"])

    def test_given_entry_with_row_field_when_parsing_then_reads_both(self):
        [c] = build.parse_contributions(["- 2026-09-30 | https://x | fixed a thing | behavior: unblocking others | row: scope.proactive-discovery"])
        self.assertEqual(c["behavior"], "unblocking others")
        self.assertEqual(c["row"], "scope.proactive-discovery")


class Build(unittest.TestCase):
    def test_given_legacy_and_career_logs_when_building_then_board_shows_entries_from_both(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            for rel, text in ((f"{LEGACY}/contributions.log.md", "# h\n\n- 2026-09-29 | https://a | legacy only | behavior: x\n"),
                              (f"{CAREER}/contributions.log.md", "# h\n\n- 2026-09-30 | https://b | career only | behavior: y | row: r.one\n")):
                p = Path(home) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            (Path(board) / "data.json").write_text(json.dumps({"scan": {}, "items": []}))
            subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home], check=True, capture_output=True)
            page = (Path(board) / "board.html").read_text()
            self.assertIn("legacy only", page)
            self.assertIn("career only", page)


if __name__ == "__main__":
    unittest.main()
