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
            self.assertIn("nothing owned", b["message"])
            self.assertIn("no project you own yet", b["message"])

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


class Board(unittest.TestCase):
    def test_given_undecided_candidates_when_building_board_data_then_lists_them_most_seen_first(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [
                {"id": "a", "title": "Partners miss order emails", "status": "candidate", "seen_count": 1, "evidence": ["https://example.com/1"]},
                {"id": "b", "title": "Toast pages missing", "status": "candidate", "seen_count": 2, "evidence": ["https://example.com/2"]},
                {"id": "c", "title": "Kept idea", "status": "proposed", "seen_count": 1, "evidence": []},
                {"id": "d", "title": "Dismissed idea", "status": "dropped", "seen_count": 1, "evidence": []},
            ])
            board = co.board(str(home), "2026-10-01")["initiatives"]
            self.assertEqual([i["id"] for i in board["candidates"]], ["b", "a"])
            self.assertEqual([i["id"] for i in board["proposed"]], ["c"])


class BoardExtras(unittest.TestCase):
    def test_given_rows_with_labels_and_next_steps_when_rating_then_carries_them(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = full_map()
            m["rubric"]["rows"][0].update({"label": "Finding problems", "next_step": "Own one problem end to end"})
            write(home, f"{CAREER}/promotion-map.json", m)
            row = next(r for r in co.readiness(str(home)) if r["id"] == "scope.proactive-discovery")
            self.assertEqual((row["label"], row["next_step"]), ("Finding problems", "Own one problem end to end"))

    def test_given_a_map_with_packet_readiness_when_building_board_data_then_includes_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = full_map(packet_readiness=[{"section": "Technical Craft", "state": "strong", "evidence_rows": [], "note": "reviews"}])
            write(home, f"{CAREER}/promotion-map.json", m)
            self.assertEqual(co.board(str(home), "2026-10-01")["packet"], [{"section": "Technical Craft", "state": "strong", "note": "reviews"}])

    def test_given_log_entries_when_building_the_trend_then_counts_eight_weeks_oldest_first(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/contributions.log.md", log(
                "- 2026-09-30 | https://example.com/1 | a | behavior: x",
                "- 2026-09-25 | https://example.com/2 | b | behavior: x",
                "- 2026-09-20 | https://example.com/3 | c | behavior: x",
                "- 2026-07-01 | https://example.com/4 | too old | behavior: x"))
            trend = co.trend(str(home), "2026-10-01")
            self.assertEqual(len(trend["weeks"]), 8)
            self.assertEqual(trend["weeks"][-1], {"ending": "2026-10-01", "count": 2})
            self.assertEqual(trend["weeks"][-2], {"ending": "2026-09-24", "count": 1})
            self.assertEqual(sum(w["count"] for w in trend["weeks"]), 3)


class BoardRecognition(unittest.TestCase):
    def test_given_a_recognition_cache_when_building_board_data_then_includes_its_summary(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/recognition.json", {"fetched_on": "2026-10-01", "received": [
                {"id": "b1", "date": "2026-09-30", "giver": {"name": "Kai", "email": "kai@example.com"}, "value": "own-the-outcome"}], "given": []})
            b = co.board(str(home), "2026-10-01")
            self.assertEqual((b["recognition"]["received"], b["recognition"]["givers"][0]["name"], b["readiness_target"]), (1, "Kai", 3))

    def test_given_no_recognition_cache_when_building_board_data_then_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(co.board(d, "2026-10-01")["recognition"], {"has_recognition": False})


class BoardMeasure(unittest.TestCase):
    def test_given_a_check_past_its_date_when_building_board_data_then_lists_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/measurements.json", [{"id": "faster-search", "work": {"title": "Faster search", "link": "https://example.com/t/1", "kind": "ticket"},
                "stage": "after", "created_at": "2026-08-01", "launch_date": "2026-09-01", "checks": [{"after_days": 14, "due": "2026-09-15", "done_at": None}]}])
            m = co.board(str(home), "2026-10-01")["measure"]
            self.assertEqual((m["has_measurements"], m["count"], m["checks_due"][0]["title"]), (True, 1, "Faster search"))

    def test_given_no_measurements_when_building_board_data_then_says_none_saved(self):
        with tempfile.TemporaryDirectory() as d:
            m = co.board(d, "2026-10-01")["measure"]
            self.assertEqual((m["has_measurements"], m["count"]), (False, 0))

    def test_given_a_broken_measurements_file_when_building_board_data_then_the_rest_still_builds(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / CAREER / "measurements.json"
            p.parent.mkdir(parents=True)
            p.write_text("{not json")
            b = co.board(d, "2026-10-01")
            self.assertIn("measurements.json", b["measure"]["error"])
            self.assertEqual(b["promotion"], {"has_map": False})

    def test_given_a_saved_check_with_a_malformed_date_when_building_board_data_then_the_rest_still_builds(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/measurements.json", [{"id": "x", "work": {"title": "X", "link": "https://example.com/x"}, "stage": "after", "checks": [{"due": 5}]}])
            b = co.board(str(home), "2026-10-01")
            self.assertEqual(([p["id"] for p in b["measure"]["problems"]], b["promotion"]), (["x"], {"has_map": False}))

    def test_given_reminders_off_when_building_board_data_then_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, ".claude/skills/flagrare/config.json", {"skills": {"measure-impact": {"reminders": "off"}}})
            self.assertFalse(co.board(str(home), "2026-10-01")["measure"]["reminders"])


class MapLine(unittest.TestCase):
    def test_given_a_map_when_summarizing_then_lists_gaps_people_and_dates(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", full_map())
            line = co.map_line(str(home))
            self.assertEqual((line["open_rows"], line["total_rows"], line["unseen_people"], line["target_level"]), (1, 2, ["Alex Chen"], "Senior Software Engineer"))
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
