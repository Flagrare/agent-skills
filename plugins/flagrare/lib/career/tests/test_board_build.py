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


class LinkTitle(unittest.TestCase):
    def test_given_a_link_with_no_known_shape_when_titling_then_names_the_host(self):
        self.assertEqual(build.link_title("https://www.example.com/some/page"), "example.com")

    def test_given_a_pull_request_link_when_titling_then_names_repo_and_number(self):
        self.assertEqual(build.link_title("https://github.com/acme/payments/pull/12#review"), "payments #12")


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

    def test_given_an_active_initiative_and_a_map_when_building_then_the_page_carries_both(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            career = Path(home) / CAREER
            career.mkdir(parents=True)
            fact = {"source": "https://example.com", "checked_at": "2026-09-30", "status": "inferred"}
            (career / "promotion-map.json").write_text(json.dumps({
                "target": {"target_level": {**fact, "value": "Senior Software Engineer"}},
                "calendar": {"packet_deadline": {**fact, "value": "2027-01-07"}},
                "rubric": {"rows": [{"id": "scope.proactive-discovery", "area": "Scope & Impact", "status": "partial", "evidence": []}]},
                "people": [{"name": "Alex Chen", "seen_your_work": False}]}))
            (career / "initiatives.json").write_text(json.dumps([{"id": "order-emails", "title": "Partners not getting order emails",
                "status": "active", "aligned": {"with": "Sam Rivera", "on": "2026-09-05"}, "evidence": ["https://example.com/1"]}]))
            (Path(board) / "data.json").write_text(json.dumps({"scan": {"date": "2026-10-01"}, "items": []}))
            subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home], check=True, capture_output=True)
            page = (Path(board) / "board.html").read_text()
            data = json.loads(page.split("/*DATA*/", 1)[1].split("/*END*/", 1)[0])
            self.assertEqual(data["career"]["initiatives"]["active"]["id"], "order-emails")
            self.assertEqual(data["career"]["promotion"]["unseen_people"], ["Alex Chen"])
            self.assertEqual([r["id"] for r in data["career"]["readiness"]], ["scope.proactive-discovery"])
            self.assertEqual(len(data["career"]["trend"]["weeks"]), 8)
            self.assertEqual(data["career"]["packet"], [])
            self.assertIn("<title>Career Board</title>", page)
            self.assertIn("fill=&#x27;%230d6b66&#x27;", page)

    def test_given_a_malformed_map_when_building_then_the_board_renders_and_carries_the_read_error(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            career = Path(home) / CAREER
            career.mkdir(parents=True)
            (career / "promotion-map.json").write_text(json.dumps({"target": "senior", "rubric": "rows"}))
            (Path(board) / "data.json").write_text(json.dumps({"scan": {}, "items": []}))
            out = subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home, "--today", "2026-10-01"], capture_output=True, text=True)
            self.assertEqual(out.returncode, 0)
            self.assertIn("career panel skipped", out.stderr)
            data = json.loads((Path(board) / "board.html").read_text().split("/*DATA*/", 1)[1].split("/*END*/", 1)[0])
            self.assertIn("error", data["career"])

    def test_given_no_career_state_when_building_then_the_page_still_renders(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            (Path(board) / "data.json").write_text(json.dumps({"scan": {}, "items": []}))
            subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home, "--today", "2026-10-01"], check=True, capture_output=True)
            data = json.loads((Path(board) / "board.html").read_text().split("/*DATA*/", 1)[1].split("/*END*/", 1)[0])
            self.assertEqual((data["career"]["promotion"], data["career"]["initiatives"]["active"]), ({"has_map": False}, None))


    def test_given_a_check_due_when_building_then_the_page_carries_the_measure_block(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            career = Path(home) / CAREER
            career.mkdir(parents=True)
            (career / "measurements.json").write_text(json.dumps([{"id": "faster-search", "work": {"title": "Faster search", "link": "https://example.com/t/1", "kind": "ticket"},
                "stage": "after", "created_at": "2026-08-01", "launch_date": "2026-09-01", "checks": [{"after_days": 14, "due": "2026-09-15", "done_at": None}]}]))
            (Path(board) / "data.json").write_text(json.dumps({"scan": {}, "items": []}))
            subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home, "--today", "2026-10-01"], check=True, capture_output=True)
            html = (Path(board) / "board.html").read_text()
            data = json.loads(html.split("/*DATA*/", 1)[1].split("/*END*/", 1)[0])
            self.assertEqual(data["career"]["measure"]["checks_due"][0]["id"], "faster-search")
            self.assertIn('id="measure-sec"', html)

if __name__ == "__main__":
    unittest.main()
