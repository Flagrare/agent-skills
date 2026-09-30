# Career skills, Milestone 3: opportunity-scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan or anything it produces (repo hook). Check with `python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" <files>`, which must print 0. Never run `scripts/check-no-emdash.py` by hand.

**Goal:** Ship `/flagrare:opportunity-scan`, which proposes two or three problems the user could own end to end (checked for an existing owner, ranked against the promotion map, each with a hypothesis, a success metric, a first step and a manager pitch), keeps at most one initiative active after manager alignment, and consumes the problems impact-scan hands off. Ships as 1.46.0.

**Architecture:** Same split as the other career skills: the library supplies inputs and plans writes, the model judges. A new `initiatives.py` flattens what the ranking needs from the promotion map (reusing `scoring.open_rows` and `scoring.unseen_people`), groups the existing initiatives by status, computes the cadence, and plans `initiatives.json` and `opportunity-state.json`. Transitions are mechanical and enforced there (one active, alignment required, dismissed stays dismissed unless seen again). Owner checks, ranking and pitches are skill-text judgment.

**Tech Stack:** Markdown skills, Python 3 stdlib, `unittest`, `evals/evals.json`.

**Spec:** `docs/plans/2026-09-30-career-skills-design.md`, section `opportunity-scan` and Milestone 3.

**Deviation from the spec, on purpose:** the spec's shared-state list has no place for a cadence timestamp. `initiatives.json` is a list (shape shipped in 1.45.0), and `scan-state.json` belongs to impact-scan (its model-written rewrites could drop a foreign key). This plan adds one small file, `career/opportunity-state.json` (`{"last_run": "YYYY-MM-DD"}`), documented in `STATE.md`. Milestone 4's scheduler reads it.

Decisions taken while designing (with the advisor):
- **Config.** Opportunity-scan reuses impact-scan's config (surfaces, domains, behaviors, audience) and onboarding. Its own block only holds `cadence_days`.
- **Owner check is a hard filter.** It is not a ranking factor.
- **Dismissed problems.** A `dropped` problem comes back only when seen after `dropped_at`, and impact-scan's Handed off line then says it was dismissed before.
- **Cadence.** An explicit run ignores the cadence. A scheduled run stops when not due.
- **Window.** The lookback is `last_run` to today, 30 days the first time, and capped at 90 days.

## Global Constraints

- No em-dashes in any file. Verify with the command above.
- Python stdlib only, `from __future__ import annotations`, system `python3`.
- Tests: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v` from the repo root. The count is the 66 existing tests plus 26 new, 92 in total.
- Library scripts never write under `~/.claude/skills/`; they print planned content for the skill to write with the Write tool (Read first when the file exists).
- The skill never posts, sends or publishes anything; sweeps are read-only.
- Every name in fixtures and evals is invented (the repo is public).
- Commits direct to `main`, gitmoji plus conventional, no attribution lines. The release commit and tag stay local until the user approves publishing.
- The board's initiative card is Milestone 4, not this plan.

## Review Focus

1. **A handed-off candidate proposed, then seen again by impact-scan:** the proposal, `seen_count` and `first_seen` all survive both writers (Task 1 test `test_given_a_proposal_when_impact_scan_sees_it_again_then_the_proposal_survives`).
2. **A second activation:** it is refused and names the active one, from the CLI too with exit code 2 (Task 1).
3. **Map facts with conflicting sources** (`alternatives`): they reach the skill as a list, and the skill shows every option (Tasks 1 and 3).
4. **No map and no previous run:** the scan still runs with a 30-day window and the impact-scan config fallback (Task 1 tests, Task 3 eval 3).
5. **A problem someone already owns:** it is cut, with the owner named, and never proposed as the user's (Task 3 eval 1).

---

## File Structure

```
plugins/flagrare/lib/career/
  career_state.py             # modify: paths() gains opportunity_state (Task 1)
  initiatives.py              # create: context, plan_propose, plan_status, plan_run, CLI (Task 1)
  tests/test_initiatives.py   # create (Task 1)
  STATE.md                    # modify: initiatives.json proposal shape and moves, opportunity-state.json (Task 2)
plugins/flagrare/skills/impact-scan/SKILL.md   # modify: hand-off paragraph points at opportunity-scan (Task 2)
plugins/flagrare/skills/opportunity-scan/
  SKILL.md                    # create (Task 3)
  evals/evals.json            # create (Task 3)
  evals/fixtures/promotion-map.json, initiatives.json, initiatives-with-active.json  # create (Task 3)
README.md, CHANGELOG.md, plugins/flagrare/.claude-plugin/plugin.json  # Task 4
```

---

### Task 1: Initiatives library

**Files:**
- Modify: `plugins/flagrare/lib/career/career_state.py` (one line in `paths()`)
- Create: `plugins/flagrare/lib/career/initiatives.py`
- Test: `plugins/flagrare/lib/career/tests/test_initiatives.py`

**Interfaces:**
- Consumes:
  - `career_state.paths`, `career_state.skill_config` and `career_state._load_list`.
  - `scoring.open_rows(map)` and `scoring.unseen_people(map)`.
  - `career_state.plan_candidate`, which is used in one test to prove the two writers coexist.
- Produces:
  - `paths(home)["opportunity_state"]` = `<home>/.claude/skills/flagrare/career/opportunity-state.json`.
  - `initiatives.context(home, today) -> dict` with these keys:
    - `has_map`, `target`, `open_rows`, `unseen_people`, `decision_process`, `packet_deadline`;
    - `initiatives{active, proposed, candidates, dropped[seen_again]}`;
    - `cadence{last_run, days_since, due, window_start}`;
    - `fallback{target_behaviors, domains, audience}`.
  - Planners that return action lists:
    - `plan_propose(home, item_id, title, evidence: list[str], proposal: dict, today) -> list[action]`;
    - `plan_status(home, item_id, status, today, aligned_with="", note="") -> list[action]`;
    - `plan_run(home, today) -> list[action]`.
  - Refusals raise `ValueError`.
  - CLI: `initiatives.py context|propose|status|run --home H --today D [--id --title --evidence (repeatable) --proposal JSON --status --aligned-with --note]`. A refusal is an argparse error (exit 2).

- [ ] **Step 1: Write the failing tests** `plugins/flagrare/lib/career/tests/test_initiatives.py`:

```python
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
            "pitch": "Two incidents in a month, same cause; I can own the fix.", "owner_check": "searched open tickets and the team channel, no owner"}


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
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'initiatives'`.

- [ ] **Step 3: Add the path.** In `career_state.py`, inside `paths()`, add this line directly after the `"flags": ...` line:

```python
        "opportunity_state": str(career / "opportunity-state.json"),
```

- [ ] **Step 4: Write `plugins/flagrare/lib/career/initiatives.py`**

```python
"""Inputs and planned writes for opportunity-scan. Never writes files.

The model still judges which problems are worth owning and how to pitch them;
this module lists what the ranking reads (the promotion map, the initiatives
already recorded, the cadence) and plans the initiatives.json and
opportunity-state.json content the skill writes with the Write tool.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

import career_state
from scoring import open_rows, unseen_people

CADENCE_DAYS = 30
WINDOW_CAP_DAYS = 90
REQUIRED = ["problem", "hypothesis", "metric", "first_step", "pitch", "owner_check"]
MOVES = {
    ("candidate", "dropped"), ("proposed", "dropped"),
    ("proposed", "active"), ("active", "done"), ("active", "dropped"),
    ("dropped", "candidate"),
}


def _value(fact: object) -> object:
    """A fact's value, every alternative's value when sources disagree, or the plain value itself."""
    if isinstance(fact, dict):
        if "value" in fact:
            return fact["value"]
        if isinstance(fact.get("alternatives"), list):
            return [a.get("value") for a in fact["alternatives"] if isinstance(a, dict)]
        return None
    return fact


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _items(home: str) -> list:
    return career_state._load_list(Path(career_state.paths(home)["initiatives"]))


def _write(path: str, data: object, reason: str) -> list[dict]:
    return [{"action": "write", "path": path, "content": json.dumps(data, indent=2, ensure_ascii=False) + "\n", "reason": reason}]


def _cadence(home: str, today: str, cadence_days: int) -> dict:
    state = _load_json(Path(career_state.paths(home)["opportunity_state"]))
    last_run = state.get("last_run") if isinstance(state, dict) else None
    now = date.fromisoformat(today)
    try:
        since = (now - date.fromisoformat(str(last_run))).days if last_run else None
    except ValueError:
        since = None
    start = now - timedelta(days=cadence_days) if since is None else now - timedelta(days=min(since, WINDOW_CAP_DAYS))
    return {"last_run": last_run if since is not None else None, "days_since": since,
            "due": since is None or since >= cadence_days, "window_start": start.isoformat()}


def context(home: str, today: str) -> dict:
    """What opportunity-scan ranks against: the map (when there is one), the initiatives so far, the cadence, and the impact-scan config as fallback."""
    p = career_state.paths(home)
    config = _load_json(Path(p["config"]))
    config = config if isinstance(config, dict) else {}
    own = career_state.skill_config(config, "opportunity-scan")
    scan = career_state.skill_config(config, "impact-scan")
    cadence_days = own.get("cadence_days", CADENCE_DAYS) if isinstance(own, dict) else CADENCE_DAYS
    scan = scan if isinstance(scan, dict) else {}
    items = [i for i in _items(home) if isinstance(i, dict) and i.get("id")]
    by_status = lambda s: [i for i in items if i.get("status") == s]
    dropped = [{**i, "seen_again": str(i.get("last_seen", "")) > str(i.get("dropped_at", ""))} for i in by_status("dropped")]
    result = {
        "has_map": False,
        "target": {}, "open_rows": [], "unseen_people": [],
        "decision_process": None, "packet_deadline": None,
        "initiatives": {
            "active": (by_status("active") or [None])[0],
            "proposed": by_status("proposed"),
            "candidates": sorted(by_status("candidate"), key=lambda i: -int(i.get("seen_count") or 0)),
            "dropped": dropped,
        },
        "cadence": _cadence(home, today, cadence_days),
        "fallback": {"target_behaviors": scan.get("target_behaviors", []), "domains": scan.get("domains", []),
                     "audience": scan.get("audience", [])},
    }
    m = _load_json(Path(p["map_json"]))
    if not isinstance(m, dict):
        return result
    target = m.get("target") or {}
    process = m.get("process") or {}
    calendar = m.get("calendar") or {}
    decision = process.get("decision_process") if isinstance(process, dict) else None
    deadline = calendar.get("packet_deadline") if isinstance(calendar, dict) else None
    result.update({
        "has_map": True,
        "target": {k: _value(target.get(k)) for k in ("target_level", "cycle", "why", "more_of", "less_of") if target.get(k) is not None},
        "open_rows": open_rows(m),
        "unseen_people": unseen_people(m),
        "decision_process": {k: _value(v) for k, v in decision.items()} if isinstance(decision, dict) else None,
        "packet_deadline": {"value": _value(deadline), "status": deadline.get("status")} if isinstance(deadline, dict) else None,
    })
    return result


def plan_propose(home: str, item_id: str, title: str, evidence: list[str], proposal: dict, today: str) -> list[dict]:
    """Plan initiatives.json with a proposal: a new item, or a candidate (or one dropped and seen again) moved to proposed, keeping its sightings."""
    missing = [k for k in REQUIRED if not proposal.get(k)]
    if missing:
        raise ValueError(f"proposal is missing {', '.join(missing)}")
    path = career_state.paths(home)["initiatives"]
    items = _items(home)
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            status = item.get("status")
            if status == "dropped" and not str(item.get("last_seen", "")) > str(item.get("dropped_at", "")):
                raise ValueError(f"{item_id} was dropped on {item.get('dropped_at')} and not seen since; reopen it first")
            if status in ("active", "done"):
                raise ValueError(f"{item_id} is already {status}")
            links = item.setdefault("evidence", [])
            links += [e for e in evidence if e and e not in links]
            item["title"] = title or item.get("title", "")
            item["proposal"] = proposal
            item["status"] = "proposed"
            item["proposed_at"] = today
            break
    else:
        links = [e for e in dict.fromkeys(evidence) if e]
        if not links:
            raise ValueError("a new proposal needs at least one evidence link")
        items.append({"id": item_id, "title": title, "evidence": links, "seen_count": len(links),
                      "first_seen": today, "last_seen": today, "status": "proposed",
                      "proposal": proposal, "proposed_at": today})
    return _write(path, items, f"propose {item_id}")


def plan_status(home: str, item_id: str, status: str, today: str, aligned_with: str = "", note: str = "") -> list[dict]:
    """Plan initiatives.json with one status change. Only one item may be active, and only after manager alignment."""
    path = career_state.paths(home)["initiatives"]
    items = _items(home)
    item = next((i for i in items if isinstance(i, dict) and i.get("id") == item_id), None)
    if item is None:
        raise ValueError(f"no initiative with id {item_id}")
    current = item.get("status")
    if (current, status) not in MOVES:
        raise ValueError(f"cannot move {item_id} from {current} to {status}")
    if status == "active":
        other = next((i for i in items if isinstance(i, dict) and i.get("status") == "active"), None)
        if other is not None:
            raise ValueError(f"{other.get('id')} is already active; finish or drop it first")
        if not aligned_with:
            raise ValueError("an initiative becomes active only after manager alignment: pass who agreed")
        item["aligned"] = {"with": aligned_with, "on": today, "note": note}
    item["status"] = status
    item[f"{status}_at"] = today
    if note and status != "active":
        item[f"{status}_note"] = note
    return _write(path, items, f"move {item_id} to {status}")


def plan_run(home: str, today: str) -> list[dict]:
    """Plan opportunity-state.json with this run's date."""
    path = career_state.paths(home)["opportunity_state"]
    state = _load_json(Path(path))
    state = state if isinstance(state, dict) else {}
    state["last_run"] = today
    return _write(path, state, "record this opportunity scan")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only helper for opportunity-scan.")
    parser.add_argument("command", choices=["context", "propose", "status", "run"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today", required=True)
    parser.add_argument("--id")
    parser.add_argument("--title", default="")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--proposal", help="the proposal fields as a JSON object")
    parser.add_argument("--status")
    parser.add_argument("--aligned-with", default="")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    try:
        if args.command == "context":
            result: object = context(args.home, args.today)
        elif args.command == "run":
            result = plan_run(args.home, args.today)
        elif args.command == "propose":
            if not (args.id and args.proposal):
                parser.error("propose needs --id and --proposal")
            try:
                proposal = json.loads(args.proposal)
            except json.JSONDecodeError as exc:
                parser.error(f"--proposal is not valid JSON: {exc}")
            if not isinstance(proposal, dict):
                parser.error("--proposal must be a JSON object")
            result = plan_propose(args.home, args.id, args.title, args.evidence, proposal, args.today)
        else:
            if not (args.id and args.status):
                parser.error("status needs --id and --status")
            result = plan_status(args.home, args.id, args.status, args.today, args.aligned_with, args.note)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 92 tests (66 plus 26).

- [ ] **Step 6: Commit**

```bash
git add plugins/flagrare/lib/career
git commit -m "✨ feat(opportunity-scan): initiatives library with proposals, one-active rule and cadence"
```

---

### Task 2: State contract and impact-scan hand-off pointer

**Files:**
- Modify: `plugins/flagrare/lib/career/STATE.md`
- Modify: `plugins/flagrare/skills/impact-scan/SKILL.md` (one sentence)

- [ ] **Step 1: Replace the whole of `STATE.md` with this content**

````markdown
# Career state files

Shared by `/flagrare:promotion`, `/flagrare:impact-scan`, `/flagrare:opportunity-scan` and the career skills that follow. They live in `~/.claude/skills/flagrare/career/`, outside the plugin tree so they survive updates. Skills write them with the Write tool (a sandboxed shell cannot write there); the scripts in this folder only read and plan. `career_state.py plan` brings over and merges anything still in the old `~/.claude/skills/flagrare/senior-scan/` folder and never deletes it.

## contributions.log.md

Append-only evidence log, one line per contribution:

```
- <YYYY-MM-DD> | <link> | <one sentence: what the contribution was and what it changed> | behavior: <target behavior exercised>
```

An optional trailing field ties the entry to a rubric row in the promotion map: `| row: <rubric row id>`, for example `| row: scope.proactive-discovery`. Readers accept lines with or without it. Never rewrite or reorder existing lines.

## scan-state.json

Impact-scan's dedupe state (formerly `senior-scan/state.json`):

```json
{ "last_run": "2026-09-30T13:30:00Z",
  "seen": [{ "id": "slack:C123:1790703452.608029", "source": "slack", "surfaced_at": "2026-09-30T13:30:00Z", "status": "surfaced|contributed|dropped|handed_off" }] }
```

When both the old and new files exist, the merge keeps the later `last_run` and the union of `seen` by `id` (the later `surfaced_at` wins, the career copy wins a tie, and a `contributed` item always wins over any other status for the same id). Items without an `id` are kept too. Other top-level keys are kept. For any other top-level key present in both files, the career value wins. A file that is not valid state is left alone rather than merged.

## voice.md

The user's observed writing rules, used for drafts. The newer of the old and new copies wins.

## promotion-map.json and promotion-map.md

Written only by `/flagrare:promotion`. Shape: `skills/promotion/reference/map-schema.md`.

## flags.json

Signals that part of the promotion map may be stale. Other skills append through `career_state.py flag`, which skips a flag when one for the same section already has the same reason or the same source; `/flagrare:promotion` reads them on refresh and removes the ones it handled.

```json
[{ "section": "org", "reason": "a new team lead was announced", "source": "<link>", "raised_at": "2026-09-30" }]
```

`section` is one of the promotion map's sections (`target`, `process`, `calendar`, `rubric`, `org`, `people`, `precedent`, `packet_readiness`, `manager_questions`).

## initiatives.json

Work the user could own. When the user has a promotion map, impact-scan records problem-type items (a recurring problem the user could fix, as opposed to a thread to answer) through `career_state.py candidate`, once per scan run: a new evidence link adds a sighting (`seen_count` goes up) and keeps the item's `status`, a link already recorded changes nothing, so the same thread continuing never counts twice. The hand-off threshold is impact-scan's rule, not the script's: at `seen_count` 2 or more it stops drafting replies for that problem and marks the scan item `handed_off` in `scan-state.json`. `/flagrare:opportunity-scan` checks each candidate for an existing owner, ranks it with its own findings, and records what the user keeps through `initiatives.py`:

- `propose` moves a candidate (or a new problem) to `proposed` and adds a `proposal` object. It keeps `seen_count`, `first_seen` and every evidence link, and `career_state.py candidate` keeps the proposal when the problem is seen again.
- `status` makes one move at a time: `candidate` or `proposed` to `dropped`, `proposed` to `active`, `active` to `done` or `dropped`, and `dropped` back to `candidate`. Each move stamps `<status>_at`.
- **At most one item is `active`, and only after manager alignment:** the script refuses a second one (naming the first) and refuses `active` without `aligned-with`, which it records as `aligned`.
- A `dropped` item is proposed again only when it was seen after `dropped_at`.

```json
[{ "id": "stable-slug", "title": "plain words", "evidence": ["<link>"], "seen_count": 2,
   "first_seen": "2026-09-25", "last_seen": "2026-09-30", "status": "candidate|proposed|active|done|dropped",
   "proposal": { "problem": "...", "hypothesis": "We believe X will Y because Z", "metric": "...", "impact": "...",
                 "who_cares": "...", "why_now": "...", "first_step": "...", "pitch": "...", "owner_check": "what was searched",
                 "decision_fit": "...", "rubric_rows": ["scope.proactive-discovery"] },
   "proposed_at": "2026-10-01", "aligned": { "with": "...", "on": "2026-10-03", "note": "..." }, "active_at": "2026-10-03",
   "dropped_at": "...", "dropped_note": "..." }]
```

## opportunity-state.json

When opportunity-scan last ran, so it (and later `/flagrare:career`) can tell when the next one is due (every `skills["opportunity-scan"].cadence_days`, default 30):

```json
{ "last_run": "2026-10-01" }
```
````

The changes from the current file are:
- the opening line names opportunity-scan;
- the `initiatives.json` section gains the proposal shape and the allowed moves;
- a new `opportunity-state.json` section.

- [ ] **Step 2: Update the impact-scan hand-off sentence.** In `plugins/flagrare/skills/impact-scan/SKILL.md`, replace exactly:

```
The candidates wait in `initiatives.json` for `/flagrare:opportunity-scan` (coming in a later release).
```

with:

```
The candidates wait in `initiatives.json` for `/flagrare:opportunity-scan`, which turns them into proposals the user could own. When the candidate's status is `dropped` (the user dismissed it in an opportunity scan), the Handed off line says so: "dismissed on <date>, seen again".
```

- [ ] **Step 3: Verify and commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/lib/career/STATE.md plugins/flagrare/skills/impact-scan/SKILL.md
git diff --stat
git add plugins/flagrare/lib/career/STATE.md plugins/flagrare/skills/impact-scan/SKILL.md
git commit -m "📝 docs(career): proposals, initiative moves and opportunity-state in the state reference"
```
Expected: `0`, and the diff touches only those two files.

---

### Task 3: The opportunity-scan skill, evals and fixtures

**Files:**
- Create: `plugins/flagrare/skills/opportunity-scan/SKILL.md`
- Create: `plugins/flagrare/skills/opportunity-scan/evals/evals.json`
- Create: `plugins/flagrare/skills/opportunity-scan/evals/fixtures/promotion-map.json`, `initiatives.json`, `initiatives-with-active.json`

The eval `files` field points at fixtures. The repo precedent is `files: []` and 1.45.0 did the same thing; whether the eval runner loads the path is still unverified, so the fixtures are there for graders and humans to read.

- [ ] **Step 1: Write `SKILL.md`** (complete file, starting with `---` on line 1)

````markdown
---
name: opportunity-scan
description: Propose two or three pieces of work the user could own end to end, instead of threads to reply to. It sweeps the org's connected surfaces (chat, tickets, docs, PRs) over the last month for recurring pain, silent degradation, ownership gaps, unanswered invitations and leadership priorities, adds the problems /flagrare:impact-scan handed off, checks that nobody already owns each one, and ranks them against the user's promotion map (what they want more and less of, which open rubric row it closes, who cares and whether they have seen the user's work, whether it can land before the target cycle). Each proposal comes with evidence links, a hypothesis and success metric set before building, the smallest first step, and a short pitch for the manager that fits how the company decides. Keeps at most one initiative active, and only after manager alignment. Runs about monthly. Use when the user says "opportunity scan", "what should I own", "what could I lead", "find me a project", "what problem should I pick up", "what would move the needle", "I want to own something end to end", or asks for work that would show next-level scope. Also trigger from /flagrare:career when the scan is due.
---

# Opportunity Scan

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

Impact-scan finds threads to weigh in on. The next level asks for more: finding a problem nobody assigned, and owning it through to a result someone can measure. This skill looks for those problems on purpose, checks nobody already owns them, and brings back two or three proposals the user could take to their manager.

The failure modes it must never enable:
- **Grabbing someone else's work.** A problem already owned is not an opportunity. The owner check runs before anything is proposed, and a proposal that skipped it is cut.
- **Going around the people who decide.** A proposal fits how the company makes decisions: if a PM drives the decision document, the first step feeds evidence into that document, never a competing one.
- **Pitching on a guess.** Every claim in a proposal has a link, or is marked as a check to run first.
- **Spreading thin.** At most one initiative is active, and it only counts as the user's after their manager agrees.

**This skill never posts, sends, or publishes anything.** Sweeps are read-only, and the pitch is a draft for the user.

## Library and state

Helper scripts live at `<plugin root>/lib/career/`, where the plugin root is two directories above this skill's base directory. Run them as `python3 <plugin root>/lib/career/<script>.py ...`. They only read and print JSON. Write every state file with the Write tool, reading it first if it exists: a sandboxed shell cannot write under `~/.claude/skills`.

- `initiatives.py context --home "$HOME" --today <YYYY-MM-DD>`: everything the ranking reads (see step 1).
- `initiatives.py propose --home "$HOME" --today <date> --id <slug> --title "<plain words>" --evidence <link> [--evidence <link> ...] --proposal '<json>'`: plans `initiatives.json` with a proposal.
- `initiatives.py status --home "$HOME" --today <date> --id <slug> --status <status> [--aligned-with "<who>"] [--note "<why>"]`: plans one status change.
- `initiatives.py run --home "$HOME" --today <date>`: plans `opportunity-state.json` with this run's date.

A script that refuses (exit code 2) prints the reason; tell the user in plain words and do not work around it. The state files' shapes are in `<plugin root>/lib/career/STATE.md`.

## Setup (every run)

1. **Load state.** Run `python3 <plugin root>/lib/career/career_state.py plan --home "$HOME"` and apply each `write` action with the Write tool, reading the target first if it exists. **Never delete anything.**
2. **Config.** Read `~/.claude/skills/flagrare/config.json`. This skill sweeps the same surfaces as impact-scan and reuses its onboarding: surfaces, domains, target behaviors and audience come from `skills["impact-scan"]` (or the older `skills["senior-scan"]`). If neither block has `onboarding_complete: true`, run the onboarding in `<plugin root>/skills/impact-scan/SKILL.md` (identity, career target, domains, surfaces; skip voice and board if the user wants to move on) and save it under `skills["impact-scan"]`. This skill's own block, `skills["opportunity-scan"]`, only holds `cadence_days` (default 30).

## Workflow

### 1. Context and cadence

Run `initiatives.py context`. It prints:

- `has_map`, and from the promotion map: `target` (`target_level`, `cycle`, `why`, `more_of`, `less_of`), `open_rows` (rubric rows not yet done), `unseen_people`, `decision_process` (`artifact`, `usual_driver`), and `packet_deadline`. A value that is a list means the map's sources disagree: show every option, never pick one.
- `initiatives`: the `active` one (or null), `proposed`, `candidates` (most seen first) and `dropped` (each with `seen_again`: seen since it was dismissed).
- `cadence`: `last_run`, `days_since`, `due`, and `window_start`, the first day to sweep (the last run, or 30 days back the first time, never more than 90 days back).
- `fallback`: the impact-scan config's `target_behaviors`, `domains` and `audience`.

**Cadence.** When the user asked for this scan, run it even if it is not due. When `/flagrare:career` or a schedule started it and `due` is false, stop and say when it is next due.

**Without a map** the scan still runs. Ranking uses the configured target behaviors and domains; the "which open row" and "before the target cycle" factors are skipped; the first step defaults to bringing the problem to the manager. Say once, in the digest header, that `/flagrare:promotion` would sharpen the ranking.

**With an active initiative**, open the digest with a one-line check-in on it (what the last evidence shows, and whether it looks done). New proposals are still made, but none can become active until the current one is done or dropped.

### 2. Sweep

Spawn **one read-only sweep subagent per configured surface**, all in the same message so they run concurrently, over `window_start` to today. Each gets its surface's scope, the domain map with keywords, the exclusions and the user's identity. Sweeps never post, react or comment.

Every sweep hunts the same five signals:

- **Recurring pain:** the same question asked again, repeat incidents with one cause, support toil, a manual step people keep doing by hand.
- **Silent degradation:** something getting slower, flakier or more expensive with nobody assigned (a flaky test everyone reruns, an alert everyone mutes, a metric trending the wrong way).
- **Ownership gaps:** a new integration or partner nobody supports, a team missing a skill it needs, work orphaned by a reorg or a departure.
- **Unanswered invitations:** "someone should look at this", "would love help with", a proposal waiting for a volunteer.
- **Leadership priorities:** themes documents, OKRs, planning docs, a new leader's stated focus. Search the docs surface for them; they tell you which problems will be noticed.

Each finding comes back as: the problem in plain words, every evidence link, who is affected, who has talked about it, and any sign of an owner (an assignee, a ticket in progress, someone saying "I'm on it").

Add the `candidates` from `initiatives.json` (the problems impact-scan handed off) to the findings, and any `dropped` item with `seen_again: true`, marked as dismissed before.

### 3. Owner check (hard filter)

For every finding, check whether someone already owns it before ranking it:

- search open tickets for the problem's keywords and linked incidents;
- search open PRs touching the systems involved;
- read the latest messages in the thread or channel where it was raised.

Record what you checked in one sentence (it becomes the proposal's `owner_check`). If someone owns it, cut it and name the owner on the digest's **Cut** line; if the owner has gone quiet for weeks, it can stay, as "offer to help or take over", never as the user's own. A finding you could not check is cut too, with the reason.

### 4. Rank

Score each surviving finding 0-2 on six factors:

- **Fit:** it matches what the user wants more of, and is not something they want less of (with no map: their configured target behaviors).
- **Rubric:** it closes one of the `open_rows`; pick the row from `open_rows` only, never invent one (no map: skip, score 1).
- **Who cares:** people who would notice the result, with extra weight when they are in `unseen_people`.
- **Standing:** the user knows the area (one of their domains, systems they have worked in).
- **Evidence:** how often it came up and from how many places; a handed-off candidate with `seen_count` 2 or more starts at 2.
- **Timing:** it can show a result before the `packet_deadline` (no map or no deadline: skip, score 1).

Drop anything scoring 0 on Standing or Evidence. Keep the top 3.

### 5. Proposals

The digest is short: the user should know what each proposal is from its first line.

```
## Opportunity scan: <date>, window <window_start> to <today>. <caveats: surfaces skipped, no map, not due but run on request>
<one line on the active initiative, when there is one>

### 1. <the problem in plain words, as the thing to own>
**Evidence:** <links, each with three words on what it shows>
**Hypothesis:** We believe <change> will <result> because <reason>. **Success:** <metric, measured how, decided before building>.
**Rough impact:** <who gets what, in plain words>. **Who cares:** <people or teams, and why now>.
**First step:** <the smallest step, fitted to how decisions are made>
**Pitch for your manager:** <three sentences at most, in the user's voice>

(repeat, at most 3)

**Cut:** <finding: reason (owned by X, could not verify, no standing)>; ...
```

Rules:

- **Fit the local decision process.** When `decision_process.usual_driver` is a PM or product role, the first step feeds evidence to them for their `artifact`, and the pitch offers to own the engineering side. When it names engineering, the first step can be a short written proposal. Without a map, the first step is bringing it to the manager.
- **Nothing on an unchecked claim.** Numbers and causes in a proposal come from a link. When one is missing, write `Check first:` with the single check instead of the claim.
- **The hypothesis comes before the build.** A proposal without a success metric is not ready: say what data would show it worked, and where that data lives.
- **Plain words.** No ticket keys or channel ids in the headline; they go in the evidence links. Rubric row ids go in parentheses after the hypothesis, only with a map.
- **Pitch in the user's voice.** Read `~/.claude/skills/flagrare/career/voice.md` when it exists. First person, no preamble, no flourish.

Stop after the Cut line. Ask which proposals to keep, which to dismiss, and whether any is already agreed with their manager.

### 6. Record

After the user answers, write each change with the Write tool, one script call at a time (each reads the file the previous one wrote):

- **Keep:** `initiatives.py propose` with the fields below. For a handed-off candidate, reuse its id so its sightings carry over.
- **Dismiss:** `initiatives.py status --status dropped --note "<why, in the user's words>"`. It will not come back unless it is seen again.
- **Agreed with the manager:** `initiatives.py status --status active --aligned-with "<who>" --note "<where or how it was agreed>"`. Only a proposal can become active, only one at a time, and never without the user saying their manager agreed. Do not suggest skipping that conversation.
- **Finished or abandoned** (when the user says so later): `--status done` or `--status dropped`.

The `--proposal` JSON holds: `problem`, `hypothesis`, `metric`, `impact`, `who_cares`, `why_now`, `first_step`, `pitch`, `owner_check`, `decision_fit` (how the first step fits the decision process), and `rubric_rows` (ids from `open_rows`, empty without a map). The script refuses a proposal missing `problem`, `hypothesis`, `metric`, `first_step`, `pitch` or `owner_check`.

Finally run `initiatives.py run` and write `opportunity-state.json`, even when nothing was kept, so the cadence counts from today. If a write fails, say so: the next scan would re-propose the same things.

When an initiative becomes active, suggest logging its milestones as contributions with `/flagrare:impact-scan` as they land; the contributions log stays the evidence trail.
````

- [ ] **Step 2: Write `evals/fixtures/promotion-map.json`**

```json
{
  "target": {
    "current_level": {
      "value": "Software Engineer III",
      "source": "https://example.com/ladder",
      "checked_at": "2026-09-30",
      "status": "verified"
    },
    "target_level": {
      "value": "Senior Software Engineer",
      "source": "https://example.com/ladder",
      "checked_at": "2026-09-30",
      "status": "verified"
    },
    "cycle": {
      "value": "January 2027",
      "source": "https://example.com/ladder",
      "checked_at": "2026-09-30",
      "status": "inferred"
    },
    "why": "more say in what we build",
    "more_of": [
      "user-facing work",
      "leading projects end to end"
    ],
    "less_of": [
      "guild and tooling work"
    ]
  },
  "process": {
    "decision_process": {
      "artifact": {
        "value": "product gate document",
        "source": "https://example.com/ladder",
        "checked_at": "2026-09-30",
        "status": "verified"
      },
      "usual_driver": {
        "value": "PM",
        "source": "https://example.com/ladder",
        "checked_at": "2026-09-30",
        "status": "verified"
      }
    }
  },
  "calendar": {
    "cycle_name": "January 2027",
    "packet_deadline": {
      "value": "2027-01-07",
      "source": "https://example.com/ladder",
      "checked_at": "2026-09-30",
      "status": "inferred"
    }
  },
  "rubric": {
    "rows": [
      {
        "id": "scope.proactive-discovery",
        "area": "Scope & Impact",
        "status": "partial",
        "current_text": {
          "value": "Given a problem, finds the right solution",
          "source": "https://example.com/ladder",
          "checked_at": "2026-09-30",
          "status": "verified"
        },
        "target_text": {
          "value": "Proactively discovers and solves problems the team is facing",
          "source": "https://example.com/ladder",
          "checked_at": "2026-09-30",
          "status": "verified"
        },
        "evidence": []
      },
      {
        "id": "craft.review-quality",
        "area": "Technical Craft",
        "status": "done",
        "current_text": {
          "value": "Timely, constructive reviewer",
          "source": "https://example.com/ladder",
          "checked_at": "2026-09-30",
          "status": "verified"
        },
        "target_text": {
          "value": "Sought-after reviewer for their stack",
          "source": "https://example.com/ladder",
          "checked_at": "2026-09-30",
          "status": "verified"
        },
        "evidence": []
      }
    ]
  },
  "people": [
    {
      "name": "Sam Rivera",
      "role": {
        "value": "Engineering Manager",
        "source": "https://example.com/ladder",
        "checked_at": "2026-09-30",
        "status": "verified"
      },
      "relation": "current manager",
      "seen_your_work": true,
      "evidence": [],
      "confirmed_by_user": true
    },
    {
      "name": "Alex Chen",
      "role": {
        "value": "Director of Engineering",
        "source": "https://example.com/ladder",
        "checked_at": "2026-09-30",
        "status": "verified"
      },
      "relation": "skip level",
      "seen_your_work": false,
      "evidence": [],
      "confirmed_by_user": true
    }
  ],
  "sections": {
    "target": {
      "checked_at": "2026-09-30",
      "sources": []
    },
    "process": {
      "checked_at": "2026-09-30",
      "sources": []
    },
    "calendar": {
      "checked_at": "2026-09-30",
      "sources": []
    },
    "rubric": {
      "checked_at": "2026-09-30",
      "sources": []
    },
    "people": {
      "checked_at": "2026-09-30",
      "sources": []
    }
  }
}
```

- [ ] **Step 3: Write `evals/fixtures/initiatives.json`**

```json
[
  {
    "id": "order-emails-missing",
    "title": "Partners not getting order emails",
    "evidence": [
      "https://example.com/incidents/41",
      "https://example.com/support/9"
    ],
    "seen_count": 2,
    "first_seen": "2026-09-23",
    "last_seen": "2026-09-30",
    "status": "candidate"
  }
]
```

- [ ] **Step 4: Write `evals/fixtures/initiatives-with-active.json`**

```json
[
  {
    "id": "flaky-checkout-tests",
    "title": "Checkout tests fail at random",
    "evidence": [
      "https://example.com/ci/3"
    ],
    "seen_count": 1,
    "first_seen": "2026-09-01",
    "last_seen": "2026-09-01",
    "status": "active",
    "proposed_at": "2026-09-02",
    "aligned": {
      "with": "Sam Rivera",
      "on": "2026-09-05",
      "note": "agreed in 1:1"
    },
    "active_at": "2026-09-05"
  },
  {
    "id": "order-emails-missing",
    "title": "Partners not getting order emails",
    "evidence": [
      "https://example.com/incidents/41",
      "https://example.com/support/9"
    ],
    "seen_count": 2,
    "first_seen": "2026-09-23",
    "last_seen": "2026-09-30",
    "status": "proposed",
    "proposed_at": "2026-10-01",
    "proposal": {
      "problem": "Partners are not getting order emails",
      "hypothesis": "We believe a delivery check will cut missed orders because failures are silent today",
      "metric": "missed-order reports per week",
      "first_step": "add the evidence to the PM's product gate document",
      "pitch": "Two incidents in a month with one cause; I'd like to own the engineering side.",
      "owner_check": "searched open tickets and the team channel, no owner",
      "decision_fit": "feeds the PM's document",
      "rubric_rows": [
        "scope.proactive-discovery"
      ]
    }
  }
]
```

- [ ] **Step 5: Write `evals/evals.json`**

```json
{
  "skill_name": "opportunity-scan",
  "evals": [
    {
      "id": 0,
      "prompt": "Run an opportunity scan. My promotion map and initiatives are in ~/.claude/skills/flagrare/career/ (see the fixtures). Nobody has picked up the order email problem as far as I know.",
      "expected_output": "Agent runs initiatives.py context, includes the handed-off candidate order-emails-missing, searches tickets, PRs and the thread for an existing owner and states what it checked, and proposes it with evidence links, a 'We believe ... because ...' hypothesis and a success metric. Because the map's decision process is driven by a PM, the first step feeds evidence into the PM's product gate document instead of writing a competing one. The rubric row id appears only in parentheses after the hypothesis, and the scan proposes at most 3 items and asks which to keep.",
      "files": [
        "evals/fixtures/promotion-map.json",
        "evals/fixtures/initiatives.json"
      ]
    },
    {
      "id": 1,
      "prompt": "Run an opportunity scan. In the support channel people keep asking why partner payouts show as pending, but there's a ticket in progress assigned to another engineer who posted an update yesterday.",
      "expected_output": "Agent finds the recurring payout question, checks for an owner, finds the in-progress ticket and the recent update, and does not propose it as the user's own: it appears on the Cut line naming the owner.",
      "files": [
        "evals/fixtures/promotion-map.json"
      ]
    },
    {
      "id": 2,
      "prompt": "My manager agreed I should take the order emails problem. Make it my active initiative.",
      "expected_output": "Agent runs initiatives.py status to make order-emails-missing active, the script refuses because flaky-checkout-tests is already active, and the agent explains in plain words that only one initiative can be active and asks whether to finish or drop the current one first. It does not edit initiatives.json by hand to get around the refusal.",
      "files": [
        "evals/fixtures/initiatives-with-active.json"
      ]
    },
    {
      "id": 3,
      "prompt": "Run an opportunity scan. I haven't built a promotion map.",
      "expected_output": "Agent runs the scan anyway, ranks with the configured target behaviors and domains, skips the rubric and target-cycle factors, makes the first step of each proposal bringing it to the manager, and says once in the header that /flagrare:promotion would sharpen the ranking.",
      "files": []
    }
  ]
}
```

- [ ] **Step 6: Verify and commit**

```bash
python3 -c "t=open('plugins/flagrare/skills/opportunity-scan/SKILL.md').read();assert t.startswith('---\nname: opportunity-scan\n');print('ok')"
python3 -c "import json,glob;[json.load(open(f)) for f in ['plugins/flagrare/skills/opportunity-scan/evals/evals.json']+glob.glob('plugins/flagrare/skills/opportunity-scan/evals/fixtures/*.json')];print('json ok')"
python3 plugins/flagrare/lib/career/map_schema.py check plugins/flagrare/skills/opportunity-scan/evals/fixtures/promotion-map.json --today 2026-10-01
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/skills/opportunity-scan/SKILL.md plugins/flagrare/skills/opportunity-scan/evals/evals.json plugins/flagrare/skills/opportunity-scan/evals/fixtures/*.json
git add plugins/flagrare/skills/opportunity-scan
git commit -m "✨ feat(opportunity-scan): propose work to own, checked for owners and ranked against the promotion map"
```
Expected: `ok`, `json ok`, a check result with `"errors": []` (missing sections are fine), and `0`.

---

### Task 4: README, CHANGELOG and local release 1.46.0

**Files:** `README.md`, `CHANGELOG.md`, `plugins/flagrare/.claude-plugin/plugin.json`

- [ ] **Step 1: README skill counts.** The README counts every skill directory except the deprecated `senior-scan` alias. With opportunity-scan that is thirty-six. Replace:
  - on line 3: `Thirty-three skills` with `Thirty-six skills`;
  - on line 5: `and twenty-eight more` with `and thirty-one more`;
  - on line 13: `all thirty-three skills` with `all thirty-six skills`.

- [ ] **Step 2: README paragraph.** Insert a new paragraph directly after the paragraph that starts "`/flagrare:impact-scan` (formerly `/flagrare:senior-scan`", with one blank line before and after:

`/flagrare:opportunity-scan` proposes work you could own end to end, instead of threads to reply to. About once a month it sweeps the same surfaces as impact-scan over the last few weeks for recurring pain, silent degradation, ownership gaps, unanswered invitations and leadership priorities, and picks up the problems impact-scan handed off. Before ranking anything it checks whether someone already owns the problem, and cuts it if so. Each of the two or three proposals that survive carries evidence links, a hypothesis and success metric set before building, the smallest first step (fitted to how your company decides, so a PM-driven decision gets your evidence instead of a competing document), and a short pitch for your manager. With a promotion map it ranks by what you want more and less of, which open rubric row the work closes, and who would notice; without one it falls back to impact-scan's config. It keeps at most one initiative active, and only after your manager agrees.

- [ ] **Step 3: Tests and README commit**

```bash
python3 -m unittest discover -s plugins/flagrare/lib/career/tests
git diff README.md | python3 -c "import sys;print(sum(l.count(chr(0x2014)) for l in sys.stdin if l.startswith('+')))"
git add README.md
git commit -m "📝 docs(readme): opportunity-scan and the corrected skill count"
```

- [ ] **Step 4: Version and CHANGELOG**

```bash
python3 scripts/bump-version.py 1.46.0
python3 -c "import json;print(json.load(open('plugins/flagrare/.claude-plugin/plugin.json'))['version'])"
```
Expected: `1.46.0`.

Insert at the top of `CHANGELOG.md`, under `# Changelog` and its blank line, above `## 1.45.0: 2026-09-30`:

```markdown
## 1.46.0: 2026-09-30

Something to own, not just something to answer.

### New Skills

- **`/flagrare:opportunity-scan`, proposals you could own end to end**: since 1.45.0, impact-scan hands off problems that keep coming back instead of drafting a third reply, and nothing picked them up: they sat in `initiatives.json`. The rubric line these career skills keep pointing at, "proactively discovers and solves problems", had no skill looking for it on purpose. Opportunity-scan does. About once a month it sweeps the connected surfaces over the last few weeks for recurring pain, silent degradation, ownership gaps, unanswered invitations and leadership priorities, adds the handed-off problems, and checks each one for an existing owner before ranking it: an owned problem is cut and the owner named. It ranks what is left by what the user wants more and less of, the open rubric row it closes, who would notice, standing in the area, how often it came up, and whether it can land before the packet deadline, and brings back at most three proposals. Each has evidence links, a "we believe X will Y because Z" hypothesis with a success metric set before building, the smallest first step, and a short pitch for the manager. The first step fits how the company decides: when a PM drives the decision document, the proposal feeds evidence into it instead of going around it. At most one initiative is active, and only after the user says their manager agreed, which is recorded. A dismissed problem stays dismissed unless it shows up again. Without a promotion map it still runs, ranking against impact-scan's config.

### Improved Skills

- **`/flagrare:impact-scan`**: the Handed off line now points at opportunity-scan, and says when a problem the user dismissed has come back.

### Tooling

- **Career library**: `initiatives.py` plans every opportunity-scan write (`context`, `propose`, `status`, `run`) and refuses a second active initiative, an activation without manager alignment, and a proposal missing its hypothesis, metric, first step, pitch or owner check. A new `opportunity-state.json` records the last run for the 30-day cadence. The README's skill count is corrected.

```

- [ ] **Step 5: Local release commit (no tag, no push)**

```bash
git diff CHANGELOG.md | python3 -c "import sys;print(sum(l.count(chr(0x2014)) for l in sys.stdin if l.startswith('+')))"
git add CHANGELOG.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "🔖 release: v1.46.0"
```
The controller tags after the final review and asks the user before pushing, the GitHub release, and `/flagrare:update`.
