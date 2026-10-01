from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import career_state as cs  # noqa: E402
import initiatives as ini  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
CONFIG = ".claude/skills/flagrare/config.json"
FACT = {"source": "https://example.com", "checked_at": "2026-09-30", "status": "verified"}
MAP = {
    "target": {"target_level": {**FACT, "value": "Senior Software Engineer"}, "more_of": ["user-facing work"], "less_of": ["guild work"]},
    "process": {"decision_process": {"artifact": {**FACT, "value": "product gate doc"}, "usual_driver": {**FACT, "value": "PM"}}},
    "calendar": {"packet_deadline": {**FACT, "value": "2027-01-07", "status": "inferred"}},
    "rubric": {"rows": [{"id": "scope.proactive-discovery", "area": "Scope & Impact", "status": "partial",
                         "target_text": {**FACT, "value": "Proactively discovers and solves problems"}}]},
    "people": [{"name": "Alex Chen", "seen_your_work": False}],
}
PROPOSAL = {"problem": "Partners miss order emails", "hypothesis": "We believe a delivery check will cut missed orders because failures are silent today",
            "metric": "missed-order reports per week", "first_step": "add the evidence to the PM's product gate doc",
            "pitch": "Two incidents in a month, same cause; I can own the fix.", "owner_check": "searched open tickets and the team channel, no owner",
            "lever": "the partner order email is sent by systems the user's squad owns"}


def write(home: Path, rel: str, data: object) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data))


def apply(actions: list[dict]) -> None:
    for a in actions:
        Path(a["path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(a["path"]).write_text(a["content"])


def candidate(**extra) -> dict:
    return {"id": "order-emails", "title": "Order emails missing", "evidence": ["https://example.com/1", "https://example.com/2"],
            "seen_count": 2, "first_seen": "2026-09-20", "last_seen": "2026-09-30", "status": "candidate", **extra}


class Context(unittest.TestCase):
    def test_given_no_map_when_reading_context_then_falls_back_to_the_impact_scan_config(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, CONFIG, {"skills": {"senior-scan": {"target_behaviors": ["unblocking others"], "domains": [{"name": "billing"}]}}})
            ctx = ini.context(str(home), "2026-10-01")
            self.assertFalse(ctx["has_map"])
            self.assertEqual(ctx["fallback"]["target_behaviors"], ["unblocking others"])
            self.assertEqual(ctx["fallback"]["domains"], [{"name": "billing"}])
            self.assertIsNone(ctx["decision_process"])

    def test_given_a_map_when_reading_context_then_flattens_the_facts_the_ranking_needs(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", MAP)
            ctx = ini.context(str(home), "2026-10-01")
            self.assertTrue(ctx["has_map"])
            self.assertEqual(ctx["target"]["more_of"], ["user-facing work"])
            self.assertEqual(ctx["target"]["target_level"], "Senior Software Engineer")
            self.assertEqual(ctx["decision_process"], {"artifact": "product gate doc", "usual_driver": "PM"})
            self.assertEqual(ctx["packet_deadline"], {"value": "2027-01-07", "status": "inferred"})
            self.assertEqual([r["id"] for r in ctx["open_rows"]], ["scope.proactive-discovery"])
            self.assertEqual(ctx["unseen_people"], ["Alex Chen"])

    def test_given_conflicting_sources_when_reading_context_then_keeps_every_alternative(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            conflict = {"status": "unverified", "alternatives": [{**FACT, "value": "PM"}, {**FACT, "value": "engineering manager"}]}
            write(home, f"{CAREER}/promotion-map.json", {"process": {"decision_process": {"usual_driver": conflict}}})
            self.assertEqual(ini.context(str(home), "2026-10-01")["decision_process"], {"usual_driver": ["PM", "engineering manager"]})

    def test_given_initiatives_when_reading_context_then_groups_them_by_status_most_seen_first(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [
                candidate(id="a", seen_count=1), candidate(id="b", seen_count=3),
                candidate(id="c", status="active"), candidate(id="e", status="proposed"),
                candidate(id="d", status="dropped", dropped_at="2026-09-25"),
                candidate(id="f", status="dropped", dropped_at="2026-09-30"),
            ])
            groups = ini.context(str(home), "2026-10-01")["initiatives"]
            self.assertEqual([i["id"] for i in groups["candidates"]], ["b", "a"])
            self.assertEqual(groups["active"]["id"], "c")
            self.assertEqual([i["id"] for i in groups["proposed"]], ["e"])
            self.assertEqual({i["id"]: i["seen_again"] for i in groups["dropped"]}, {"d": True, "f": False})


class Priorities(unittest.TestCase):
    def test_given_company_priorities_in_the_map_when_reading_context_then_lists_each_metric_and_the_users_lever(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            m = {**MAP, "priorities": [
                {"theme": "Merchant trust", "metric": {**FACT, "value": "share of merchants confused by their statements"},
                 "baseline": {**FACT, "value": "27% confused"}, "owner_team": "Merchants", "user_lever": "input"},
                {"theme": "Grow orders", "metric": {**FACT, "value": "orders per active member"}, "owner_team": "Growth", "user_lever": "none"},
            ]}
            write(home, f"{CAREER}/promotion-map.json", m)
            prios = ini.context(str(home), "2026-10-01")["priorities"]
            self.assertEqual(prios[0], {"theme": "Merchant trust", "metric": "share of merchants confused by their statements",
                                        "baseline": "27% confused", "target": None, "owner_team": "Merchants", "user_lever": "input"})
            self.assertEqual(prios[1]["user_lever"], "none")

    def test_given_no_priorities_when_reading_context_then_the_list_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(ini.context(d, "2026-10-01")["priorities"], [])

    def test_given_a_proposal_without_a_lever_when_proposing_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "lever"):
                ini.plan_propose(d, "x", "t", ["https://example.com/1"], {k: v for k, v in PROPOSAL.items() if k != "lever"}, "2026-10-01")


def scored(impact, **rest):
    base = {f: 1 for f in ini.FACTORS}
    base.update(rest)
    base["impact"] = impact
    return {f: {"value": v, "why": f"{f} reason"} for f, v in base.items()}


class Ranking(unittest.TestCase):
    def test_given_a_score_when_totalling_then_impact_counts_double(self):
        total, top = ini.score_total(scored(2, lever=2, fit=2, rubric=2, who_notices=2, standing=2, evidence=2, timing=2))
        self.assertEqual((total, top), (18, 18))
        self.assertEqual(ini.score_total(scored(1))[0], 9)

    def test_given_custom_weights_when_totalling_then_uses_them(self):
        total, top = ini.score_total(scored(2, fit=2), {"impact": 2, "fit": 2})
        self.assertEqual((total, top), (2 * 2 + 2 * 2 + 6 * 1, 20))

    def test_given_candidates_with_scores_when_reading_context_then_ranks_by_total_and_marks_fixes(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [
                candidate(id="small", seen_count=3, draft_proposal={"score": scored(0)}),
                candidate(id="big", seen_count=1, draft_proposal={"score": scored(2, lever=2)}),
                candidate(id="mid", seen_count=1, draft_proposal={"score": scored(1)}),
                candidate(id="unscored", seen_count=5),
            ])
            groups = ini.context(str(home), "2026-10-01")["initiatives"]
            self.assertEqual([i["id"] for i in groups["candidates"]], ["big", "mid", "small", "unscored"])
            ranks = {i["id"]: i["rank"] for i in groups["candidates"]}
            self.assertEqual((ranks["big"]["total"], ranks["big"]["max"], ranks["small"]["is_fix"], ranks["unscored"]["total"]), (12, 18, True, None))

    def test_given_a_score_outside_zero_to_two_when_proposing_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            bad = {**PROPOSAL, "score": scored(3)}
            with self.assertRaisesRegex(ValueError, "0, 1 or 2"):
                ini.plan_propose(d, "x", "t", ["https://example.com/1"], bad, "2026-10-01")

    def test_given_an_unknown_factor_when_proposing_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            bad = {**PROPOSAL, "score": {"vibes": {"value": 2, "why": "x"}}}
            with self.assertRaisesRegex(ValueError, "vibes"):
                ini.plan_propose(d, "x", "t", ["https://example.com/1"], bad, "2026-10-01")


class Cadence(unittest.TestCase):
    def test_given_no_previous_run_when_reading_context_then_is_due_with_a_30_day_window(self):
        with tempfile.TemporaryDirectory() as d:
            cad = ini.context(d, "2026-10-01")["cadence"]
            self.assertEqual((cad["due"], cad["last_run"], cad["window_start"]), (True, None, "2026-09-01"))

    def test_given_a_run_ten_days_ago_when_reading_context_then_is_not_due_and_the_window_starts_there(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-21"})
            cad = ini.context(str(home), "2026-10-01")["cadence"]
            self.assertEqual((cad["due"], cad["days_since"], cad["window_start"]), (False, 10, "2026-09-21"))

    def test_given_a_run_ten_days_ago_when_reading_context_then_says_when_the_next_one_is_due(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-21"})
            cad = ini.context(str(home), "2026-10-01")["cadence"]
            self.assertEqual((cad["cadence_days"], cad["next_due"]), (30, "2026-10-21"))

    def test_given_a_run_long_ago_when_reading_context_then_the_window_is_capped_at_90_days(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-01-01"})
            cad = ini.context(str(home), "2026-10-01")["cadence"]
            self.assertEqual((cad["due"], cad["window_start"]), (True, "2026-07-03"))

    def test_given_a_custom_cadence_when_reading_context_then_uses_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, CONFIG, {"skills": {"opportunity-scan": {"cadence_days": 7}}})
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-21"})
            self.assertTrue(ini.context(str(home), "2026-10-01")["cadence"]["due"])

    def test_given_a_last_run_dated_tomorrow_when_reading_context_then_treats_it_as_today(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-10-02"})
            cad = ini.context(str(home), "2026-10-01")["cadence"]
            self.assertEqual((cad["due"], cad["days_since"], cad["window_start"]), (False, 0, "2026-10-01"))

    def test_given_a_cadence_written_as_text_when_reading_context_then_uses_the_number_or_the_default(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-21"})
            write(home, CONFIG, {"skills": {"opportunity-scan": {"cadence_days": "7"}}})
            self.assertTrue(ini.context(str(home), "2026-10-01")["cadence"]["due"])
            write(home, CONFIG, {"skills": {"opportunity-scan": {"cadence_days": "monthly"}}})
            self.assertFalse(ini.context(str(home), "2026-10-01")["cadence"]["due"])

    def test_given_a_run_when_recording_it_then_keeps_other_keys(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/opportunity-state.json", {"last_run": "2026-09-01", "note": "x"})
            [a] = ini.plan_run(str(home), "2026-10-01")
            self.assertEqual(json.loads(a["content"]), {"last_run": "2026-10-01", "note": "x"})


class Propose(unittest.TestCase):
    def test_given_a_handed_off_candidate_when_proposing_then_keeps_its_sightings_and_adds_the_proposal(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate()])
            [a] = ini.plan_propose(str(home), "order-emails", "", ["https://example.com/2", "https://example.com/3"], PROPOSAL, "2026-10-01")
            [item] = json.loads(a["content"])
            self.assertEqual((item["status"], item["seen_count"], item["first_seen"], item["title"]), ("proposed", 2, "2026-09-20", "Order emails missing"))
            self.assertEqual(item["evidence"], ["https://example.com/1", "https://example.com/2", "https://example.com/3"])
            self.assertEqual((item["proposal"], item["proposed_at"]), (PROPOSAL, "2026-10-01"))

    def test_given_a_proposal_when_impact_scan_sees_it_again_then_the_proposal_survives(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate()])
            apply(ini.plan_propose(str(home), "order-emails", "", [], PROPOSAL, "2026-10-01"))
            [a] = cs.plan_candidate(str(home), "order-emails", "Order emails missing", "https://example.com/9", "2026-10-02")
            [item] = json.loads(a["content"])
            self.assertEqual((item["status"], item["proposal"], item["seen_count"]), ("proposed", PROPOSAL, 3))

    def test_given_a_missing_field_when_proposing_then_names_what_is_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "owner_check"):
                ini.plan_propose(d, "x", "t", ["https://example.com/1"], {k: v for k, v in PROPOSAL.items() if k != "owner_check"}, "2026-10-01")

    def test_given_a_new_problem_without_evidence_when_proposing_then_rejects_it(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                ini.plan_propose(d, "x", "t", [], PROPOSAL, "2026-10-01")

    def test_given_a_new_problem_when_proposing_then_counts_each_evidence_link_as_a_sighting(self):
        with tempfile.TemporaryDirectory() as d:
            [a] = ini.plan_propose(d, "x", "Slow partner search", ["https://example.com/1", "https://example.com/1", "https://example.com/2"], PROPOSAL, "2026-10-01")
            [item] = json.loads(a["content"])
            self.assertEqual((item["seen_count"], item["status"], item["evidence"]), (2, "proposed", ["https://example.com/1", "https://example.com/2"]))

    def test_given_a_dismissed_problem_not_seen_since_when_proposing_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="dropped", dropped_at="2026-09-30")])
            with self.assertRaisesRegex(ValueError, "dropped"):
                ini.plan_propose(str(home), "order-emails", "", [], PROPOSAL, "2026-10-01")

    def test_given_a_dismissed_problem_seen_again_when_proposing_then_allows_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="dropped", dropped_at="2026-09-25")])
            [a] = ini.plan_propose(str(home), "order-emails", "", [], PROPOSAL, "2026-10-01")
            self.assertEqual(json.loads(a["content"])[0]["status"], "proposed")


class Status(unittest.TestCase):
    def test_given_a_proposal_when_activating_without_alignment_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="proposed")])
            with self.assertRaisesRegex(ValueError, "manager alignment"):
                ini.plan_status(str(home), "order-emails", "active", "2026-10-01")

    def test_given_a_proposal_when_activating_with_alignment_then_records_who_agreed(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="proposed")])
            [a] = ini.plan_status(str(home), "order-emails", "active", "2026-10-01", "my manager", "agreed in our 1:1")
            [item] = json.loads(a["content"])
            self.assertEqual((item["status"], item["active_at"]), ("active", "2026-10-01"))
            self.assertEqual(item["aligned"], {"with": "my manager", "on": "2026-10-01", "note": "agreed in our 1:1"})

    def test_given_blank_alignment_when_activating_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="proposed")])
            with self.assertRaisesRegex(ValueError, "manager alignment"):
                ini.plan_status(str(home), "order-emails", "active", "2026-10-01", "   ")

    def test_given_one_active_when_activating_another_then_refuses_and_names_the_active_one(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(id="first", status="active"), candidate(id="second", status="proposed")])
            with self.assertRaisesRegex(ValueError, "first is already active"):
                ini.plan_status(str(home), "second", "active", "2026-10-01", "my manager")

    def test_given_a_candidate_when_activating_directly_then_refuses_the_move(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate()])
            with self.assertRaisesRegex(ValueError, "cannot move"):
                ini.plan_status(str(home), "order-emails", "active", "2026-10-01", "my manager")

    def test_given_a_proposal_when_the_user_dismisses_it_then_records_when_and_why(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="proposed")])
            [a] = ini.plan_status(str(home), "order-emails", "dropped", "2026-10-01", note="another team owns it")
            [item] = json.loads(a["content"])
            self.assertEqual((item["status"], item["dropped_at"], item["dropped_note"]), ("dropped", "2026-10-01", "another team owns it"))

    def test_given_a_dismissed_problem_that_came_back_when_dismissing_again_then_restamps_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(status="dropped", dropped_at="2026-09-25")])
            [a] = ini.plan_status(str(home), "order-emails", "dropped", "2026-10-01", note="still not mine")
            [item] = json.loads(a["content"])
            self.assertEqual((item["status"], item["dropped_at"], item["dropped_note"]), ("dropped", "2026-10-01", "still not mine"))

    def test_given_an_unknown_id_when_changing_status_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "no initiative"):
                ini.plan_status(d, "nope", "dropped", "2026-10-01")


class Cli(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(Path(ini.__file__)), *args], capture_output=True, text=True)

    def test_given_an_empty_home_when_running_context_then_prints_json(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_cli("context", "--home", d, "--today", "2026-10-01")
            self.assertEqual(out.returncode, 0)
            self.assertFalse(json.loads(out.stdout)["has_map"])

    def test_given_a_second_active_when_running_status_then_exits_with_the_reason(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", [candidate(id="first", status="active"), candidate(id="second", status="proposed")])
            out = self.run_cli("status", "--home", d, "--today", "2026-10-01", "--id", "second", "--status", "active", "--aligned-with", "my manager")
            self.assertEqual(out.returncode, 2)
            self.assertIn("first is already active", out.stderr)

    def test_given_proposal_json_when_running_propose_then_plans_the_write(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_cli("propose", "--home", d, "--today", "2026-10-01", "--id", "x", "--title", "t",
                               "--evidence", "https://example.com/1", "--proposal", json.dumps(PROPOSAL))
            self.assertEqual(out.returncode, 0)
            self.assertEqual(json.loads(json.loads(out.stdout)[0]["content"])[0]["status"], "proposed")


class Paths(unittest.TestCase):
    def test_given_home_when_resolving_paths_then_includes_the_opportunity_state_file(self):
        self.assertTrue(cs.paths("/h")["opportunity_state"].endswith("flagrare/career/opportunity-state.json"))


if __name__ == "__main__":
    unittest.main()
