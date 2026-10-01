from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import coordinator as co  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
FACT = {"source": "https://example.com", "checked_at": "2026-09-30", "status": "verified"}
FRESH = {"checked_at": "2026-09-30", "sources": []}
SECTIONS = ["target", "process", "calendar", "rubric", "org", "people", "precedent", "packet_readiness", "manager_questions"]


def full_map(**over) -> dict:
    m = {s: {} for s in SECTIONS}
    m["people"] = [{"name": "Alex Chen", "seen_your_work": False}, {"name": "Sam Rivera", "seen_your_work": True}]
    m["manager_questions"] = []
    m["target"] = {"target_level": {**FACT, "value": "Senior Software Engineer"}}
    m["calendar"] = {"packet_deadline": {**FACT, "value": "2027-01-07", "status": "inferred"},
                     "manager_conversation": {"comfortable_by": "2026-10-30", "absolute_by": "2026-11-14", "status": "inferred", "state": "ok"}}
    m["rubric"] = {"rows": [
        {"id": "scope.proactive-discovery", "area": "Scope & Impact", "status": "partial", "target_text": FACT, "evidence": []},
        {"id": "craft.review-quality", "area": "Technical Craft", "status": "done", "target_text": FACT, "evidence": ["a", "b", "c"]},
    ]}
    m["sections"] = {s: dict(FRESH) for s in SECTIONS}
    m.update(over)
    return m


def write(home: Path, rel: str, data: object) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data if isinstance(data, str) else json.dumps(data))


def log(*lines: str) -> str:
    return "# Contributions\n\n" + "\n".join(lines) + "\n"


class Due(unittest.TestCase):
    def test_given_no_map_when_planning_a_run_then_promotion_first_run_needs_the_user_and_impact_scan_always_runs(self):
        with tempfile.TemporaryDirectory() as d:
            steps = co.due(d, "2026-10-01")
            self.assertEqual([(s["skill"], s["mode"], s["needs_user"]) for s in steps],
                             [("promotion", "first_run", True), ("opportunity-scan", "scan", False), ("impact-scan", "scan", False)])

    def test_given_a_fresh_map_and_a_recent_opportunity_scan_when_planning_then_only_impact_scan_runs(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", full_map())
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-25"})
            self.assertEqual([s["skill"] for s in co.due(str(home), "2026-10-01")], ["impact-scan"])

    def test_given_a_flagged_section_when_planning_then_refreshes_it_without_asking(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", full_map())
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-25"})
            write(home, f"{CAREER}/flags.json", [{"section": "calendar", "reason": "HR published the calendar", "source": "https://example.com/hr", "raised_at": "2026-09-30"}])
            [promo, _] = co.due(str(home), "2026-10-01")
            self.assertEqual((promo["mode"], promo["sections"], promo["needs_user"]), ("refresh", ["calendar"], False))
            self.assertIn("flagged", promo["why"])

    def test_given_a_flagged_people_section_when_planning_then_the_refresh_needs_the_user(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", full_map())
            write(home, f"{CAREER}/flags.json", [{"section": "people", "reason": "a new director", "source": "", "raised_at": "2026-09-30"}])
            self.assertTrue(co.due(str(home), "2026-10-01")[0]["needs_user"])

    def test_given_a_section_older_than_90_days_when_planning_then_refreshes_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = full_map()
            m["sections"]["org"] = {"checked_at": "2026-05-01", "sources": []}
            write(home, f"{CAREER}/promotion-map.json", m)
            promo = co.due(str(home), "2026-10-01")[0]
            self.assertEqual((promo["skill"], promo["sections"]), ("promotion", ["org"]))

    def test_given_an_interrupted_first_run_when_planning_then_resumes_it_with_the_user(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = full_map()
            for s in ("org", "people", "precedent", "packet_readiness", "manager_questions"):
                del m[s]
            write(home, f"{CAREER}/promotion-map.json", m)
            promo = co.due(str(home), "2026-10-01")[0]
            self.assertEqual((promo["mode"], promo["needs_user"]), ("resume", True))
            self.assertEqual(promo["sections"][:2], ["org", "people"])


class Balance(unittest.TestCase):
    def test_given_many_contributions_and_no_initiative_when_checking_then_warns(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/contributions.log.md", log(*[f"- 2026-09-2{i} | https://example.com/{i} | answered | behavior: unblocking others" for i in range(3)]))
            b = co.balance(str(home), "2026-10-01")
            self.assertTrue(b["warn"])
            self.assertIn("All answering, nothing owned", b["message"])

    def test_given_an_active_initiative_when_checking_then_does_not_warn(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/contributions.log.md", log(*[f"- 2026-09-2{i} | https://example.com/{i} | answered | behavior: x" for i in range(5)]))
            write(home, f"{CAREER}/initiatives.json", [{"id": "mine", "status": "active"}])
            b = co.balance(str(home), "2026-10-01")
            self.assertEqual((b["warn"], b["active"]), (False, "mine"))

    def test_given_old_contributions_only_when_checking_then_counts_only_the_window(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/contributions.log.md", log(*[f"- 2026-07-0{i} | https://example.com/{i} | answered | behavior: x" for i in range(1, 6)]))
            b = co.balance(str(home), "2026-10-01")
            self.assertEqual((b["contributions"], b["warn"]), (0, False))


class Readiness(unittest.TestCase):
    def test_given_tagged_log_entries_when_rating_rows_then_counts_them_with_the_rows_own_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", full_map())
            write(home, f"{CAREER}/contributions.log.md", log(
                "- 2026-09-20 | https://example.com/1 | found a silent failure | behavior: quality bar | row: scope.proactive-discovery",
                "- 2026-09-21 | https://example.com/2 | answered | behavior: unblocking others"))
            rows = {r["id"]: (r["evidence"], r["state"]) for r in co.readiness(str(home))}
            self.assertEqual(rows, {"scope.proactive-discovery": (1, "thin"), "craft.review-quality": (3, "strong")})

    def test_given_no_map_when_rating_rows_then_returns_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(co.readiness(d), [])


class MapLine(unittest.TestCase):
    def test_given_a_map_when_summarizing_then_lists_gaps_people_and_dates(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", full_map())
            line = co.map_line(str(home))
            self.assertEqual((line["open_rows"], line["unseen_people"], line["target_level"]), (1, ["Alex Chen"], "Senior Software Engineer"))
            self.assertEqual(line["talk_to_manager"]["absolute_by"], "2026-11-14")
            self.assertEqual(line["packet_deadline"], {"value": "2027-01-07", "status": "inferred"})

    def test_given_no_map_when_summarizing_then_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(co.map_line(d), {"has_map": False})


class Cli(unittest.TestCase):
    def test_given_an_empty_home_when_running_due_then_prints_the_steps(self):
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run([sys.executable, str(Path(co.__file__)), "due", "--home", d, "--today", "2026-10-01"],
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(json.loads(out)[-1]["skill"], "impact-scan")

    def test_given_a_bad_date_when_running_then_exits_with_a_usage_error(self):
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run([sys.executable, str(Path(co.__file__)), "due", "--home", d, "--today", "October"], capture_output=True, text=True)
            self.assertEqual(out.returncode, 2)


if __name__ == "__main__":
    unittest.main()
