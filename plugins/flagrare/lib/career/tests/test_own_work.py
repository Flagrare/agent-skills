from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1]
PLUGIN = LIB.parents[1]
CAREER = ".claude/skills/flagrare/career"
TODAY = "2026-10-27"
DOC = "https://app.notion.com/p/test-orders-design"
MEETING = "https://notes.granola.ai/d/standup-oct-20"


def pr(n: int, day: str, *keys: str, links: tuple[str, ...] = ()) -> dict:
    return {"source": "github", "link": f"https://github.com/acme/admin/pull/{n}", "title": f"[{keys[0]}] part {n}",
            "date": day, "keys": list(keys), "links": list(links)}


ITEMS = [
    pr(1, "2026-10-21", "SKU-1034", "SKU-1033", links=(DOC,)),
    pr(2, "2026-10-22", "SKU-1035", "SKU-1033"),
    pr(3, "2026-10-23", "SKU-1036", "SKU-1033"),
    {"source": "notion", "link": DOC, "title": "Admin SKU test orders", "date": "2026-10-14", "keys": [], "links": []},
    {"source": "granola", "link": MEETING, "title": "SKU standup", "date": "2026-10-20", "keys": ["SKU-1033"], "links": []},
]
MAP = {"rubric": {"rows": [{"id": "execution.lead", "area": "Execution", "label": "Leading complex projects",
                            "status": "partial", "evidence": []}]}}


def run(script: str, *args: str, ok: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run([sys.executable, str(LIB / script), *args], capture_output=True, text=True)
    if ok and p.returncode != 0:
        raise AssertionError(p.stderr)
    return p


def apply(actions: list[dict]) -> None:
    for a in actions:
        if a["action"] == "write":
            Path(a["path"]).parent.mkdir(parents=True, exist_ok=True)
            Path(a["path"]).write_text(a["content"], encoding="utf-8")


def write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def log_lines(home: str) -> list[str]:
    p = Path(home) / CAREER / "contributions.log.md"
    return [l for l in p.read_text().splitlines() if l.startswith("- ")] if p.exists() else []


class Harness:
    """A user's home with a promotion map and a board, and the own-work commands run as the skill runs them."""

    def __init__(self, home: str, board: str):
        self.home, self.board = home, Path(board)
        write_json(Path(home) / CAREER / "promotion-map.json", MAP)
        write_json(self.board / "data.json", {"scan": {"date": TODAY}, "items": []})

    def group(self, items: list[dict]) -> list[dict]:
        f = write_json(Path(self.home) / "items.json", items)
        return json.loads(run("own_work.py", "group", "--home", self.home, "--items", str(f), "--today", TODAY).stdout)

    def record(self, stream: dict, milestone: bool = False, what: str = "Took onboarding's test order blocker from a spike to an 8-PR stack",
               date: str | None = None) -> list[dict]:
        rec = [{"stream": stream["id"], "title": "SKU test orders", "link": DOC, "what": what,
                "behavior": "owning technical decisions in my domains", "row": "execution.lead",
                "members": stream["members"], "milestone": milestone, "date": date}]
        f = write_json(Path(self.home) / "records.json", rec)
        actions = json.loads(run("own_work.py", "record", "--home", self.home, "--records", str(f), "--today", TODAY).stdout)
        apply(actions)
        return actions

    def build(self) -> dict:
        run("board/build.py", str(self.board), "--home", self.home, "--today", TODAY)
        page = (self.board / "board.html").read_text()
        return json.loads(re.search(r"/\*DATA\*/(.*?)/\*END\*/", page, re.S).group(1).replace("<\\/", "</"))

    def coordinator(self, command: str) -> object:
        return json.loads(run("coordinator.py", command, "--home", self.home, "--today", TODAY).stdout)


class OwnWorkEndToEnd(unittest.TestCase):
    def test_given_my_prs_doc_and_a_meeting_on_one_epic_when_harvested_then_the_board_shows_one_project_entry_that_is_not_answering(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            [stream] = h.group(ITEMS)
            self.assertEqual(len(stream["members"]), 5)
            self.assertEqual(stream["id"], "sku-1033")
            h.record(stream, date="2026-10-26")

            [line] = log_lines(home)
            self.assertTrue(line.startswith("- 2026-10-26 | "))
            [entry] = h.build()["contributions"]
            self.assertEqual(entry["project"], "SKU test orders")
            bal = h.coordinator("balance")
            self.assertEqual(bal["contributions"], 0)
            self.assertEqual(bal["own_work"], 1)
            [row] = h.coordinator("readiness")
            self.assertEqual(row["evidence"], 1)


class NoDuplicates(unittest.TestCase):
    def test_given_a_logged_project_when_harvested_again_then_nothing_new_is_proposed(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            h.record(h.group(ITEMS)[0])
            self.assertEqual(h.group(ITEMS), [])

    def test_given_a_new_pr_on_a_logged_project_when_recorded_then_it_joins_the_project_without_a_new_entry_unless_it_is_a_milestone(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            first = h.group(ITEMS)[0]
            h.record(first)
            [again] = h.group(ITEMS + [pr(4, "2026-10-26", "SKU-1039", "SKU-1033")])
            self.assertEqual(again["id"], first["id"])
            self.assertEqual(again["new_links"], ["https://github.com/acme/admin/pull/4"])

            h.record(again)
            self.assertEqual(len(log_lines(home)), 1)
            h.record(again, milestone=True, what="All 8 test order PRs approved by the squad")
            self.assertEqual(len(log_lines(home)), 2)

    def test_given_a_project_already_logged_by_hand_when_recorded_then_it_joins_without_a_second_entry(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            p = Path(home) / CAREER / "contributions.log.md"
            p.write_text(f"# Contributions\n\n- 2026-10-15 | {DOC} | wrote it up by hand | behavior: quality bar\n")
            h.record(h.group(ITEMS)[0])
            self.assertEqual(len(log_lines(home)), 1)
            self.assertEqual(h.coordinator("balance")["own_work"], 1)

    def test_given_a_pipe_in_the_story_when_recording_then_it_is_refused(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            stream = h.group(ITEMS)[0]
            rec = [{"stream": stream["id"], "title": "x", "link": DOC, "what": "a | b", "behavior": "y", "members": stream["members"]}]
            f = write_json(Path(home) / "records.json", rec)
            p = run("own_work.py", "record", "--home", home, "--records", str(f), "--today", TODAY, ok=False)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(log_lines(home), [])


class Reopen(unittest.TestCase):
    def test_given_items_about_a_project_i_built_when_reopening_then_what_i_did_is_done_open_ones_are_tagged_and_others_stay(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            h.record(h.group(ITEMS)[0])
            write_json(h.board / "data.json", {"scan": {"date": TODAY}, "items": [
                {"id": "test-orders", "status": "dropped", "updated_on": "2026-10-08", "action": "Bring Andrea an option for test orders", "link": DOC},
                {"id": "no-date", "status": "dropped", "action": "Send the doc to a mentor", "link": DOC},
                {"id": "loose-end", "status": "todo", "action": "Re-ping on roles", "link": DOC + "?d=comment-1"},
                {"id": "other", "status": "dropped", "updated_on": "2026-10-08", "action": "Something else", "link": "https://example.com/x"},
            ]})
            apply(json.loads(run("own_work.py", "reopen", "--home", home, "--board", str(h.board / "data.json"), "--today", TODAY).stdout))

            items = {i["id"]: i for i in h.build()["items"]}
            self.assertEqual(items["test-orders"]["status"], "done")
            self.assertIn("SKU test orders", items["test-orders"]["note"])
            self.assertEqual(items["no-date"]["status"], "dropped")
            self.assertEqual(items["loose-end"]["status"], "todo")
            self.assertIn("Part of your project: SKU test orders", items["loose-end"]["note"])
            self.assertEqual(items["other"]["status"], "dropped")
            self.assertNotIn("note", items["other"])


class AlreadyBuilding(unittest.TestCase):
    def test_given_a_candidate_i_am_building_when_linked_then_it_is_marked_but_still_not_mine_without_my_manager(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            h = Harness(home, board)
            h.record(h.group(ITEMS)[0])
            write_json(Path(home) / CAREER / "initiatives.json", [
                {"id": "sku-onboarding-test-orders", "title": "Onboarding can't place a test order", "evidence": [DOC],
                 "seen_count": 1, "first_seen": "2026-10-08", "last_seen": "2026-10-08", "status": "candidate"},
                {"id": "unrelated", "title": "Something else", "evidence": ["https://example.com/y"],
                 "seen_count": 1, "first_seen": "2026-10-08", "last_seen": "2026-10-08", "status": "candidate"},
            ])
            apply(json.loads(run("own_work.py", "link-candidates", "--home", home, "--today", TODAY).stdout))

            board_data = h.coordinator("board")
            building = board_data["own_work"]["building_candidates"]
            self.assertEqual([c["id"] for c in building], ["sku-onboarding-test-orders"])
            cands = {c["id"]: c for c in board_data["initiatives"]["candidates"]}
            self.assertEqual(cands["sku-onboarding-test-orders"]["status"], "candidate")
            self.assertNotIn("building", cands["unrelated"])
            p = run("initiatives.py", "status", "--home", home, "--id", "sku-onboarding-test-orders",
                    "--status", "active", "--today", TODAY, ok=False)
            self.assertNotEqual(p.returncode, 0)


class SkillWiring(unittest.TestCase):
    def test_given_the_skills_when_reading_them_then_the_own_work_step_and_its_digest_lines_are_there(self):
        scan = (PLUGIN / "skills/impact-scan/SKILL.md").read_text()
        career = (PLUGIN / "skills/career/SKILL.md").read_text()
        template = (LIB / "board/template.html").read_text()
        for phrase in ("Your own work", "own_work.py group", "own_work.py record", "own_work.py reopen",
                       "own_work.py link-candidates", "Logged from your work"):
            self.assertIn(phrase, scan)
        for phrase in ("Logged from your work", "already building"):
            self.assertIn(phrase, career)
        for phrase in ("Your project", "already building this"):
            self.assertIn(phrase, template)


if __name__ == "__main__":
    unittest.main()
