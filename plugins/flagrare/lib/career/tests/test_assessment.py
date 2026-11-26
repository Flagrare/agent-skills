from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LIB))
import coordinator as co  # noqa: E402
import map_schema  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
FACT = {"source": "https://example.com", "checked_at": "2026-09-30", "status": "verified"}
FRESH = {"checked_at": "2026-11-01", "sources": []}
SECTIONS = ["target", "process", "calendar", "rubric", "org", "people", "precedent", "packet_readiness", "manager_questions"]


def row(rid: str, label: str, assessment: dict | None = None, status: str = "partial", next_step: str = "") -> dict:
    r = {"id": rid, "area": "Area", "label": label, "status": status, "target_text": FACT, "current_text": FACT,
         "evidence": [], "next_step": next_step}
    if assessment is not None:
        r["assessment"] = assessment
    return r


def rated_map(rows: list[dict], months: int | None = 6, effective: str | None = "2027-03-01") -> dict:
    m = {s: {} for s in SECTIONS}
    m["people"] = []
    m["manager_questions"] = []
    m["target"] = {"target_level": {**FACT, "value": "Senior Engineer"}}
    if months is not None:
        m["process"] = {"bar": {**FACT, "value": {"months": months, "text": "meet the next level for about six months"}}}
    if effective is not None:
        m["calendar"] = {"effective": {**FACT, "value": effective}}
    m["rubric"] = {"rows": rows}
    m["sections"] = {s: dict(FRESH) for s in SECTIONS}
    return m


def meets(since: str, checked: str = "2026-11-11", current: str = "meets") -> dict:
    return {"target": "meets", "current": current, "since": since, "reason": "shown in two projects",
            "proof": ["https://example.com/pr/1"], "checked_at": checked}


def not_yet(checked: str = "2026-11-11", current: str = "meets", reason: str = "no interviews yet") -> dict:
    return {"target": "not_yet", "current": current, "reason": reason, "proof": [], "checked_at": checked}


def write(home: Path, rel: str, data: object) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data if isinstance(data, str) else json.dumps(data))


def log(*lines: str) -> str:
    return "# Contributions\n\n" + "\n".join(lines) + "\n"


class MetCountAndBar(unittest.TestCase):
    def test_given_three_of_four_behaviors_met_when_reading_the_board_then_counts_them_and_checks_each_against_the_bar(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([
                row("scope.find", "Finding problems", meets("2026-07-01")),
                row("craft.review", "Reviewing", meets("2026-08-15")),
                row("craft.docs", "Design docs", meets("2026-11-01")),
                row("team.interviews", "Interviewing", not_yet(), next_step="Sign up for one interview loop"),
            ]))
            a = co.board(str(home), "2026-11-12")["assessment"]
            self.assertEqual((a["met"], a["total"], a["rated"]), (3, 4, 4))
            self.assertEqual(a["bar"]["met_by"], "2026-09-01")
            self.assertEqual(a["bar"]["months"], 6)
            self.assertEqual(a["bar"]["effective"], "2027-03-01")
            by_id = {r["id"]: r for r in a["rows"]}
            self.assertTrue(by_id["scope.find"]["holds"])
            self.assertTrue(by_id["craft.review"]["holds"])
            self.assertFalse(by_id["craft.docs"]["holds"])
            self.assertEqual(by_id["scope.find"]["months_held"], 4)
            self.assertEqual(by_id["craft.docs"]["months_held"], 0)
            self.assertEqual((a["holding"], a["short"]), (2, 1))
            self.assertEqual(a["not_yet"], [{"id": "team.interviews", "label": "Interviewing",
                                             "reason": "no interviews yet", "next_step": "Sign up for one interview loop"}])

    def test_given_no_bar_recorded_when_reading_the_board_then_counts_met_rows_without_judging_time(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([row("scope.find", "Finding problems", meets("2026-07-01"))],
                                                               months=None, effective=None))
            a = co.board(str(home), "2026-11-12")["assessment"]
            self.assertEqual(a["met"], 1)
            self.assertIsNone(a["bar"]["met_by"])
            self.assertIsNone(a["rows"][0]["holds"])


class RerateWhenProofMoves(unittest.TestCase):
    def test_given_new_tagged_proof_and_an_old_rating_when_planning_then_rerates_those_rows_without_asking(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([
                row("scope.find", "Finding problems", not_yet(checked="2026-11-01")),
                row("team.interviews", "Interviewing", not_yet(checked="2026-10-20")),
                row("craft.docs", "Design docs", meets("2026-07-01", checked="2026-11-11")),
            ]))
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-11-10"})
            write(home, f"{CAREER}/contributions.log.md",
                  log("- 2026-11-10 | https://x | found a bug | behavior: finding problems | row: scope.find",
                      "- 2026-11-05 | https://y | wrote a doc | behavior: docs | row: craft.docs"))
            [step] = [s for s in co.due(str(home), "2026-11-12") if s["skill"] == "promotion"]
            self.assertEqual(step["mode"], "refresh")
            self.assertIn("rubric", step["sections"])
            self.assertEqual(step["rows"], ["scope.find", "team.interviews"])
            self.assertFalse(step["needs_user"])
            self.assertIn("Finding problems", step["why"])
            self.assertIn("Interviewing", step["why"])

    def test_given_every_row_freshly_rated_with_no_new_proof_when_planning_then_no_promotion_step(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([row("craft.docs", "Design docs", meets("2026-07-01"))]))
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-11-10"})
            self.assertEqual([s["skill"] for s in co.due(str(home), "2026-11-12")], ["impact-scan"])

    def test_given_a_flagged_section_and_rows_due_when_planning_then_one_promotion_step_covers_both(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([row("team.interviews", "Interviewing", not_yet(checked="2026-10-01"))]))
            write(home, f"{CAREER}/flags.json", [{"section": "people", "reason": "new manager", "source": "https://z", "raised_at": "2026-11-11"}])
            steps = [s for s in co.due(str(home), "2026-11-12") if s["skill"] == "promotion"]
            self.assertEqual(len(steps), 1)
            self.assertEqual(set(steps[0]["sections"]), {"people", "rubric"})
            self.assertEqual(steps[0]["rows"], ["team.interviews"])


class ExceedingAtCurrentLevel(unittest.TestCase):
    def test_given_rows_rated_exceeding_at_the_current_level_when_reading_the_board_then_lists_them_whatever_the_target_rating(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([
                row("scope.find", "Finding problems", meets("2026-07-01", current="exceeds")),
                row("craft.review", "Reviewing", not_yet(current="exceeds")),
                row("team.interviews", "Interviewing", not_yet(current="below")),
            ]))
            a = co.board(str(home), "2026-11-12")["assessment"]
            self.assertEqual([r["label"] for r in a["exceeding"]], ["Finding problems", "Reviewing"])


class ValidationAndOlderMaps(unittest.TestCase):
    def test_given_an_unknown_rating_or_meets_without_a_since_date_when_checking_then_reports_both(self):
        bad = rated_map([
            row("scope.find", "Finding problems", {"target": "maybe", "current": "meets", "checked_at": "2026-11-11"}),
            row("craft.review", "Reviewing", {"target": "meets", "current": "meets", "checked_at": "2026-11-11"}),
        ])
        errors = map_schema.validate(bad)
        self.assertTrue(any("rubric.rows[0].assessment" in e and "target" in e for e in errors), errors)
        self.assertTrue(any("rubric.rows[1].assessment" in e and "since" in e for e in errors), errors)

    def test_given_a_map_with_no_ratings_when_checking_then_it_passes(self):
        m = rated_map([row("scope.find", "Finding problems", status="done")])
        self.assertEqual(map_schema.validate(m), [])

    def test_given_a_map_with_no_ratings_when_reading_the_board_then_counts_done_rows_as_met(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = rated_map([row("scope.find", "Finding problems", status="done"),
                           row("team.interviews", "Interviewing", status="not_started", next_step="Do one interview")])
            write(home, f"{CAREER}/promotion-map.json", m)
            a = co.board(str(home), "2026-11-12")["assessment"]
            self.assertEqual((a["met"], a["total"], a["rated"]), (1, 2, 0))
            self.assertEqual([r["label"] for r in a["not_yet"]], ["Interviewing"])

    def test_given_the_cli_when_asking_for_the_assessment_then_prints_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([row("scope.find", "Finding problems", meets("2026-07-01"))]))
            out = subprocess.run([sys.executable, str(LIB / "coordinator.py"), "assessment", "--home", str(home), "--today", "2026-11-12"],
                                 capture_output=True, text=True, check=True).stdout
            self.assertEqual(json.loads(out)["met"], 1)


class ValidationBranches(unittest.TestCase):
    def check(self, assessment: dict) -> list[str]:
        return map_schema.validate(rated_map([row("scope.find", "Finding problems", assessment)]))

    def test_given_an_unknown_current_level_rating_when_checking_then_reports_it(self):
        self.assertTrue(any("current" in e for e in self.check({**not_yet(), "current": "great"})))

    def test_given_since_after_the_rating_date_when_checking_then_reports_it(self):
        self.assertTrue(any("since is after checked_at" in e for e in self.check(meets("2026-12-01", checked="2026-11-11"))))

    def test_given_a_malformed_since_on_a_not_yet_row_when_checking_then_reports_it(self):
        self.assertTrue(any("since must be an ISO date" in e for e in self.check({**not_yet(), "since": "last spring"})))

    def test_given_no_rating_date_when_checking_then_reports_it(self):
        bad = not_yet()
        del bad["checked_at"]
        self.assertTrue(any("checked_at" in e for e in self.check(bad)))

    def test_given_an_assessment_that_is_not_an_object_when_checking_then_reports_it(self):
        self.assertTrue(any("must be an object" in e for e in self.check("meets")))


class BarEdges(unittest.TestCase):
    def met_by(self, effective: str, months: object) -> str | None:
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = rated_map([row("scope.find", "Finding problems", meets("2026-07-01"))], effective=effective)
            m["process"]["bar"]["value"]["months"] = months
            write(home, f"{CAREER}/promotion-map.json", m)
            return co.board(str(home), "2026-11-12")["assessment"]["bar"]["met_by"]

    def test_given_an_effective_date_at_month_end_when_counting_back_then_lands_on_the_last_day_of_a_shorter_month(self):
        self.assertEqual(self.met_by("2027-08-31", 6), "2027-02-28")
        self.assertEqual(self.met_by("2028-08-31", 6), "2028-02-29")

    def test_given_a_bar_of_zero_months_when_counting_back_then_the_date_is_the_effective_date(self):
        self.assertEqual(self.met_by("2027-03-01", 0), "2027-03-01")

    def test_given_a_negative_or_non_number_bar_when_reading_then_no_date_is_judged(self):
        self.assertIsNone(self.met_by("2027-03-01", -2))
        self.assertIsNone(self.met_by("2027-03-01", True))
        self.assertIsNone(self.met_by("2027-03-01", "six"))

    def test_given_a_behavior_met_exactly_on_the_bar_date_when_reading_then_it_holds(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([row("scope.find", "Finding problems", meets("2026-09-01"))]))
            self.assertTrue(co.board(str(home), "2026-11-12")["assessment"]["rows"][0]["holds"])


class RerateEdges(unittest.TestCase):
    def due(self, rows: list[dict], log_text: str = "", flags: list | None = None) -> list[dict]:
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map(rows))
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-11-10"})
            if log_text:
                write(home, f"{CAREER}/contributions.log.md", log_text)
            if flags:
                write(home, f"{CAREER}/flags.json", flags)
            return [s for s in co.due(str(home), "2026-11-12") if s["skill"] == "promotion"]

    def test_given_a_rating_exactly_14_days_old_when_planning_then_it_is_not_due_yet(self):
        self.assertEqual(self.due([row("scope.find", "Finding problems", not_yet(checked="2026-10-29"))]), [])

    def test_given_a_rating_15_days_old_when_planning_then_it_is_due(self):
        [step] = self.due([row("scope.find", "Finding problems", not_yet(checked="2026-10-28"))])
        self.assertEqual(step["rows"], ["scope.find"])

    def test_given_proof_logged_the_same_day_as_the_rating_when_planning_then_it_is_not_new(self):
        steps = self.due([row("scope.find", "Finding problems", not_yet(checked="2026-11-10"))],
                         log("- 2026-11-10 | https://x | a find | behavior: b | row: scope.find"))
        self.assertEqual(steps, [])

    def test_given_a_row_never_rated_when_planning_then_it_is_due_as_not_rated_yet(self):
        [step] = self.due([row("scope.find", "Finding problems")])
        self.assertEqual(step["rows"], ["scope.find"])
        self.assertIn("not rated yet", step["why"])

    def test_given_a_flag_that_needs_the_user_and_rows_due_when_planning_then_the_step_still_needs_the_user(self):
        [step] = self.due([row("scope.find", "Finding problems")],
                          flags=[{"section": "target", "reason": "new goal", "source": "https://z", "raised_at": "2026-11-11"}])
        self.assertTrue(step["needs_user"])
        self.assertEqual(step["sections"], ["target", "rubric"])

    def test_given_no_map_when_planning_then_the_first_run_gets_no_rows_to_rate(self):
        with tempfile.TemporaryDirectory() as d:
            [step] = [s for s in co.due(d, "2026-11-12") if s["skill"] == "promotion"]
            self.assertEqual(step["mode"], "first_run")
            self.assertNotIn("rows", step)


class FullBuild(unittest.TestCase):
    def test_given_a_rated_map_when_building_the_board_then_the_page_carries_the_assessment(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as board:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", rated_map([
                row("scope.find", "Finding problems", meets("2026-07-01")),
                row("team.interviews", "Interviewing", not_yet()),
            ]))
            Path(board, "data.json").write_text(json.dumps({"scan": {"date": "2026-11-12"}, "items": []}))
            subprocess.run([sys.executable, str(LIB / "board" / "build.py"), board, "--home", str(home)],
                           capture_output=True, text=True, check=True)
            page = Path(board, "board.html").read_text()
            data = json.loads(page.split("/*DATA*/", 1)[1].split("/*END*/", 1)[0])
            assessment = data["career"]["assessment"]
            self.assertEqual((assessment["met"], assessment["total"], assessment["holding"]), (1, 2, 1))
            self.assertEqual([r["label"] for r in assessment["not_yet"]], ["Interviewing"])


if __name__ == "__main__":
    unittest.main()
