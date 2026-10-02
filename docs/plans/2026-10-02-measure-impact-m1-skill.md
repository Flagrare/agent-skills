# Measure impact, Milestone 1: the skill and its saved file. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan's output. Check a file with `grep -n $'\u2014' <files>` (no output means clean).

**Goal:** Ship `/flagrare:measure-impact`: a skill that measures the impact of a piece of work before, after or long after it ships, backed by a plan-only helper that saves each measurement and answers "what is due today".

**Architecture:** A new plan-only script, `lib/career/measurements.py`, owns `career/measurements.json` the same way `career_state.py` owns `initiatives.json`: it validates, merges and prints planned writes as JSON, and the skill writes the file with the Write tool. The skill (`skills/measure-impact/SKILL.md`) carries the method (stages, nine thinking steps, confidence levels, verdicts, sizes, rules) and calls the script for every state change. Reminders (hooks), hand-offs from other skills and the board card are Milestones 2 to 4 and are out of scope here.

**Tech Stack:** Python 3 standard library (`argparse`, `json`, `re`, `datetime`, `pathlib`), `unittest`; Markdown skill files; the repo's `evals/evals.json` format.

**Spec:** `docs/plans/2026-10-02-measure-impact-design.md` (approved 2026-10-02). Read its sections "The skill", "Saved state" and "Testing" before starting.

## Global Constraints

- No em-dashes in any file this plan creates or edits; check with `grep -n $'\u2014' <files>` (no output means clean). The repo's `scripts/check-no-emdash.py` is a hook that reads hook JSON from stdin, not a file checker.
- Library scripts never write files; they print `[{"action": "write", "path": ..., "content": ..., "reason": ...}]` and the skill applies them with the Write tool.
- Fixtures and test data are invented. No real company, person, venue or metric names (use Kai, Sam, Alex, "team-first", "Merchant trust", "Acme Pizza", and similar).
- Test names describe behavior: `test_given_<state>_when_<action>_then_<outcome>`.
- Dates are `YYYY-MM-DD` strings everywhere; checks fall 14 and 42 days after launch; a before-stage bet with no launch date is "waiting" after 30 days.
- Stages: `before`, `after`, `past`, `skipped`. Confidence levels: `direct`, `supported`, `inferred`, `speculative`, `unknown`. Ownership: `mine`, `team`, `contributed`. Work kinds: `ticket`, `tdd`, `project`, `log_entry`. Verdicts: `worked`, `didnt_work`, `cant_tell`.
- Queries are stored verbatim and must never contain a credential.
- Commits use gitmoji conventional commits straight to `main`, with no AI attribution lines.
- Run all library tests from `plugins/flagrare/lib/career`: `python3 -m unittest discover -s tests -q`.

## Review Focus

1. **A corrupt `measurements.json`** (hand-edited, half-written): every planning command must refuse with a clear error instead of planning a write that replaces the user's file with an almost empty list. Test in Task 1.
2. **Planning the same measurement twice** (the skill re-runs after a failed write): the second call updates the entry with the same id, never appends a duplicate, and keeps checks already done. Test in Task 2.
3. **Contributions-log lines that don't match the usual shape** (no link, a link with a trailing `)` or `.`, extra spaces): `due` must not crash and must still match the link against measured work. Test in Task 4.
4. **Re-launching** (the launch date was wrong and is set again): checks already done stay as they are; only undone checks move. Test in Task 3.
5. **A query that contains a credential** (`Authorization: Bearer abc`, `password=...`): refused before anything is planned, and the error never echoes the secret. Test in Task 2.

---

## File structure

- Create `plugins/flagrare/lib/career/measurements.py`: the plan-only helper (validation, upsert, launch, check, skip, due, CLI).
- Create `plugins/flagrare/lib/career/tests/test_measurements.py`: its tests.
- Modify `plugins/flagrare/lib/career/career_state.py`: add `"measurements"` to `paths()`.
- Create `plugins/flagrare/skills/measure-impact/SKILL.md`: the skill.
- Create `plugins/flagrare/skills/measure-impact/evals/evals.json` and `plugins/flagrare/skills/measure-impact/evals/fixtures/` (`config.json`, `promotion-map.json`, `contributions.log.md`, `measurements.json`).
- Modify `plugins/flagrare/lib/career/STATE.md` (new `measurements.json` section) and `plugins/flagrare/lib/career/GLOSSARY.md` (four rows).
- Modify `CHANGELOG.md` and `plugins/flagrare/.claude-plugin/plugin.json` (release, Task 6).

---

### Task 1: Load and validate measurements

**Files:**
- Modify: `plugins/flagrare/lib/career/career_state.py` (the `paths()` dict)
- Create: `plugins/flagrare/lib/career/measurements.py`
- Test: `plugins/flagrare/lib/career/tests/test_measurements.py`

**Interfaces:**
- Consumes: `career_state.paths(home) -> dict[str, str]`.
- Produces:
  - constants `STAGES`, `CONFIDENCE`, `OWNERSHIP`, `KINDS`, `VERDICTS`, `CHECK_DAYS = (14, 42)`, `BET_WAIT_DAYS = 30`;
  - `class CorruptFile(ValueError)`;
  - `load(home: str) -> list[dict]` (missing file is `[]`; unparsable or non-list raises `CorruptFile`);
  - `check_entry(entry: dict) -> None` (raises `ValueError` with a plain message).

- [ ] **Step 1: Add the path**

In `career_state.paths()`, add one key after `"voice"`:

```python
        "measurements": str(career / "measurements.json"),
```

- [ ] **Step 2: Write the failing tests**

Create `plugins/flagrare/lib/career/tests/test_measurements.py`:

```python
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import measurements as m  # noqa: E402

CAREER = ".claude/skills/flagrare/career"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def entry(**over) -> dict:
    base = {
        "id": "acme-reorder",
        "work": {"title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket"},
        "stage": "before",
        "metric": {"name": "repeat orders per week", "why": "the button exists to bring people back"},
        "source": {"category": "data warehouse", "tool": "warehouse", "query": "select count(*) from orders", "run_at": "2026-10-01"},
        "baseline": {"value": "120 a week", "as_of": "2026-10-01", "confidence": "direct"},
        "bet": {"sentence": "We believe a reorder button will lift repeat orders, because Kai's survey says people retype orders", "range": "130 to 160 a week", "confidence": "inferred"},
        "ownership": "mine",
    }
    base.update(over)
    return base


class Load(unittest.TestCase):
    def test_given_no_file_when_loading_then_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.load(d), [])

    def test_given_a_valid_file_when_loading_then_returns_its_entries(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([entry()]))
            self.assertEqual(m.load(d)[0]["id"], "acme-reorder")

    def test_given_a_corrupt_file_when_loading_then_refuses_instead_of_returning_empty(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{not json")
            with self.assertRaises(m.CorruptFile):
                m.load(d)

    def test_given_a_file_that_is_not_a_list_when_loading_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "{}")
            with self.assertRaises(m.CorruptFile):
                m.load(d)


class CheckEntry(unittest.TestCase):
    def test_given_a_complete_entry_when_checking_then_accepts_it(self):
        m.check_entry(entry())

    def test_given_an_unknown_stage_when_checking_then_names_the_allowed_stages(self):
        with self.assertRaisesRegex(ValueError, "stage must be one of"):
            m.check_entry(entry(stage="during"))

    def test_given_an_unknown_confidence_level_when_checking_then_refuses(self):
        bad = entry(baseline={"value": "120", "as_of": "2026-10-01", "confidence": "pretty sure"})
        with self.assertRaisesRegex(ValueError, "baseline confidence must be one of"):
            m.check_entry(bad)

    def test_given_an_unknown_ownership_when_checking_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "ownership must be one of"):
            m.check_entry(entry(ownership="everyone"))

    def test_given_work_without_a_title_when_checking_then_refuses(self):
        with self.assertRaisesRegex(ValueError, "work needs a title"):
            m.check_entry(entry(work={"title": "", "link": "x", "kind": "ticket"}))

    def test_given_a_badly_formatted_date_when_checking_then_refuses(self):
        bad = entry(baseline={"value": "120", "as_of": "Oct 1", "confidence": "direct"})
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            m.check_entry(bad)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to see them fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: error, `ModuleNotFoundError: No module named 'measurements'`.

- [ ] **Step 4: Write the minimal implementation**

Create `plugins/flagrare/lib/career/measurements.py`:

```python
"""Measurements of the impact of the user's work, for /flagrare:measure-impact.

Plan-only, like career_state.py: nothing here writes a file. Commands print planned writes
of career/measurements.json as JSON, and the skill applies them with the Write tool.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path

import career_state

STAGES = ["before", "after", "past", "skipped"]
CONFIDENCE = ["direct", "supported", "inferred", "speculative", "unknown"]
OWNERSHIP = ["mine", "team", "contributed"]
KINDS = ["ticket", "tdd", "project", "log_entry"]
VERDICTS = ["worked", "didnt_work", "cant_tell"]
CHECK_DAYS = (14, 42)
BET_WAIT_DAYS = 30
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class CorruptFile(ValueError):
    """measurements.json exists but can't be read; never plan over it."""


def file_path(home: str) -> Path:
    return Path(career_state.paths(home)["measurements"])


def load(home: str) -> list[dict]:
    path = file_path(home)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CorruptFile(f"{path} is not valid JSON ({exc.msg}); fix or move it before measuring again") from exc
    if not isinstance(data, list):
        raise CorruptFile(f"{path} must hold a list of measurements")
    return data


def _check_date(name: str, value: object) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise ValueError(f"{name} must be a date written YYYY-MM-DD")
    date.fromisoformat(value)


def _check_confidence(name: str, block: object) -> None:
    if not isinstance(block, dict) or "confidence" not in block:
        return
    if block["confidence"] not in CONFIDENCE:
        raise ValueError(f"{name} confidence must be one of {CONFIDENCE}")


def check_entry(entry: dict) -> None:
    if not isinstance(entry, dict) or not entry.get("id"):
        raise ValueError("a measurement needs an id")
    work = entry.get("work") or {}
    if not work.get("title"):
        raise ValueError("work needs a title")
    if work.get("kind") not in KINDS:
        raise ValueError(f"work kind must be one of {KINDS}")
    if entry.get("stage") not in STAGES:
        raise ValueError(f"stage must be one of {STAGES}")
    if "ownership" in entry and entry["ownership"] not in OWNERSHIP:
        raise ValueError(f"ownership must be one of {OWNERSHIP}")
    for name in ("baseline", "comparable", "bet", "result"):
        _check_confidence(name, entry.get(name))
    _check_date("baseline as_of", (entry.get("baseline") or {}).get("as_of"))
    _check_date("source run_at", (entry.get("source") or {}).get("run_at"))
    _check_date("launch_date", entry.get("launch_date"))
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: `OK` (10 tests).

- [ ] **Step 6: Run the whole suite**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`, nothing else broken by the new path key.

- [ ] **Step 7: Commit**

```bash
git add plugins/flagrare/lib/career/career_state.py plugins/flagrare/lib/career/measurements.py plugins/flagrare/lib/career/tests/test_measurements.py
git commit -m "✨ feat(measure-impact): load and validate saved measurements"
```

---

### Task 2: Plan a new or updated measurement

**Files:**
- Modify: `plugins/flagrare/lib/career/measurements.py`
- Test: `plugins/flagrare/lib/career/tests/test_measurements.py`

**Interfaces:**
- Consumes: `load`, `check_entry`, `file_path`.
- Produces:
  - `plan_upsert(home: str, entry: dict, today: str) -> list[dict]`: one write action. It adds a new entry, or replaces the top-level keys given for an existing id. It always keeps the existing `checks` and `launch_date` unless the new entry gives them. It stamps `created_at` (first time) and `updated_at`.
  - `_write(home, items, reason) -> list[dict]` (shared by later tasks).
  - `check_query(query: str) -> None`: refuses credentials.

- [ ] **Step 1: Write the failing tests**

Append to `test_measurements.py`, before the `if __name__` line:

```python
def applied(actions: list[dict]) -> list[dict]:
    assert len(actions) == 1 and actions[0]["action"] == "write"
    return json.loads(actions[0]["content"])


class PlanUpsert(unittest.TestCase):
    def test_given_no_file_when_planning_then_writes_the_entry_with_its_query_verbatim(self):
        with tempfile.TemporaryDirectory() as d:
            q = "select count(*)\n  from orders where venue = 'acme'  -- kept as typed"
            items = applied(m.plan_upsert(d, entry(source={"category": "data warehouse", "tool": "warehouse", "query": q, "run_at": "2026-10-01"}), "2026-10-02"))
            self.assertEqual(items[0]["source"]["query"], q)
            self.assertEqual((items[0]["created_at"], items[0]["updated_at"]), ("2026-10-02", "2026-10-02"))

    def test_given_the_same_id_when_planning_again_then_updates_instead_of_duplicating(self):
        with tempfile.TemporaryDirectory() as d:
            first = applied(m.plan_upsert(d, entry(), "2026-10-01"))
            first[0]["checks"] = [{"due": "2026-10-15", "done_at": "2026-10-15", "value": "150", "verdict": "worked"}]
            first[0]["launch_date"] = "2026-10-01"
            write(Path(d), f"{CAREER}/measurements.json", json.dumps(first))
            items = applied(m.plan_upsert(d, entry(bet={"sentence": "We believe more", "range": "140 to 170", "confidence": "inferred"}), "2026-10-03"))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["bet"]["range"], "140 to 170")
            self.assertEqual(items[0]["checks"][0]["verdict"], "worked")
            self.assertEqual((items[0]["created_at"], items[0]["updated_at"]), ("2026-10-01", "2026-10-03"))

    def test_given_a_query_with_a_credential_when_planning_then_refuses_without_echoing_it(self):
        with tempfile.TemporaryDirectory() as d:
            bad = entry(source={"category": "api", "tool": "http", "query": "curl -H 'Authorization: Bearer abc123secret' https://api.example", "run_at": "2026-10-01"})
            with self.assertRaises(ValueError) as ctx:
                m.plan_upsert(d, bad, "2026-10-02")
            self.assertNotIn("abc123secret", str(ctx.exception))

    def test_given_a_password_in_a_query_when_planning_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            bad = entry(source={"category": "db", "tool": "psql", "query": "psql postgres://u:pw@h/db password=hunter2", "run_at": "2026-10-01"})
            with self.assertRaisesRegex(ValueError, "credential"):
                m.plan_upsert(d, bad, "2026-10-02")

    def test_given_a_corrupt_file_when_planning_then_refuses_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{oops")
            with self.assertRaises(m.CorruptFile):
                m.plan_upsert(d, entry(), "2026-10-02")
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: errors, `AttributeError: module 'measurements' has no attribute 'plan_upsert'`.

- [ ] **Step 3: Implement**

Append to `measurements.py`:

```python
SECRET_RE = re.compile(
    r"(authorization\s*:|bearer\s+\S|password\s*[=:]|passwd\s*[=:]|api[_-]?key\s*[=:]|secret\s*[=:]|token\s*[=:]|://[^/\s:@]+:[^/\s@]+@)",
    re.IGNORECASE,
)


def check_query(query: str) -> None:
    if query and SECRET_RE.search(query):
        raise ValueError("the query looks like it contains a credential; save it without the secret (use an env var or a connection name)")


def _write(home: str, items: list[dict], reason: str) -> list[dict]:
    return [{"action": "write", "path": str(file_path(home)),
             "content": json.dumps(items, indent=2, ensure_ascii=False) + "\n", "reason": reason}]


def plan_upsert(home: str, entry: dict, today: str) -> list[dict]:
    _check_date("today", today)
    check_entry(entry)
    check_query((entry.get("source") or {}).get("query", ""))
    items = load(home)
    for i, current in enumerate(items):
        if isinstance(current, dict) and current.get("id") == entry["id"]:
            merged = {**current, **entry}
            for keep in ("checks", "launch_date", "created_at"):
                if keep not in entry and keep in current:
                    merged[keep] = current[keep]
            merged["updated_at"] = today
            items[i] = merged
            return _write(home, items, f"update measurement {entry['id']}")
    items.append({**entry, "created_at": today, "updated_at": today})
    return _write(home, items, f"save measurement {entry['id']}")
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: `OK` (15 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/lib/career/measurements.py plugins/flagrare/lib/career/tests/test_measurements.py
git commit -m "✨ feat(measure-impact): save a measurement with its query, never a credential"
```

---

### Task 3: Launch, check and skip

**Files:**
- Modify: `plugins/flagrare/lib/career/measurements.py`
- Test: `plugins/flagrare/lib/career/tests/test_measurements.py`

**Interfaces:**
- Consumes: `load`, `_write`, `_check_date`, `CHECK_DAYS`, `VERDICTS`, `KINDS`.
- Produces:
  - `plan_launch(home: str, item_id: str, launch_date: str, today: str) -> list[dict]`;
  - `plan_check(home: str, item_id: str, due: str, value: str, verdict: str, today: str) -> list[dict]` (sets the check's `done_at`, `value`, `verdict`, and the entry's `stage` to `after`);
  - `plan_skip(home: str, item_id: str, title: str, link: str, kind: str, reason: str, today: str) -> list[dict]` (adds or updates a `skipped` entry).

- [ ] **Step 1: Write the failing tests**

Append to `test_measurements.py`:

```python
def saved(home: str, items: list[dict]) -> None:
    write(Path(home), f"{CAREER}/measurements.json", json.dumps(items))


class PlanLaunch(unittest.TestCase):
    def test_given_a_launch_date_when_launching_then_checks_fall_two_and_six_weeks_later(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry()])
            items = applied(m.plan_launch(d, "acme-reorder", "2026-10-01", "2026-10-02"))
            self.assertEqual(items[0]["launch_date"], "2026-10-01")
            self.assertEqual([c["due"] for c in items[0]["checks"]], ["2026-10-15", "2026-11-12"])

    def test_given_a_done_check_when_relaunching_then_keeps_it_and_moves_only_undone_ones(self):
        with tempfile.TemporaryDirectory() as d:
            done = {"due": "2026-10-15", "done_at": "2026-10-15", "value": "150", "verdict": "worked"}
            saved(d, [entry(launch_date="2026-10-01", checks=[done, {"due": "2026-11-12", "done_at": None, "value": None, "verdict": None}])])
            items = applied(m.plan_launch(d, "acme-reorder", "2026-10-08", "2026-10-16"))
            self.assertEqual(items[0]["checks"][0], done)
            self.assertEqual(items[0]["checks"][1]["due"], "2026-11-19")

    def test_given_an_unknown_id_when_launching_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "no measurement with id"):
                m.plan_launch(d, "nope", "2026-10-01", "2026-10-02")


class PlanCheck(unittest.TestCase):
    def test_given_a_due_check_when_recording_it_then_marks_it_done_and_the_entry_after(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(launch_date="2026-10-01", checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            items = applied(m.plan_check(d, "acme-reorder", "2026-10-15", "150 a week", "worked", "2026-10-16"))
            self.assertEqual(items[0]["checks"][0], {"due": "2026-10-15", "done_at": "2026-10-16", "value": "150 a week", "verdict": "worked"})
            self.assertEqual(items[0]["stage"], "after")

    def test_given_an_unknown_verdict_when_recording_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            with self.assertRaisesRegex(ValueError, "verdict must be one of"):
                m.plan_check(d, "acme-reorder", "2026-10-15", "150", "great", "2026-10-16")

    def test_given_no_check_on_that_date_when_recording_then_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            with self.assertRaisesRegex(ValueError, "no check due on 2026-10-20"):
                m.plan_check(d, "acme-reorder", "2026-10-20", "150", "worked", "2026-10-21")


class PlanSkip(unittest.TestCase):
    def test_given_a_small_fix_when_skipping_then_records_it_with_the_reason(self):
        with tempfile.TemporaryDirectory() as d:
            items = applied(m.plan_skip(d, "typo-fix", "Fix a typo on the menu page", "https://tracker.example/T-9", "ticket", "small fix, nothing users notice", "2026-10-02"))
            self.assertEqual((items[0]["stage"], items[0]["skipped_reason"]), ("skipped", "small fix, nothing users notice"))

    def test_given_an_existing_measurement_when_skipping_then_keeps_its_history(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry()])
            items = applied(m.plan_skip(d, "acme-reorder", "Reorder button for Acme Pizza", "https://tracker.example/T-1", "ticket", "dropped from the sprint", "2026-10-02"))
            self.assertEqual(len(items), 1)
            self.assertEqual((items[0]["stage"], items[0]["bet"]["range"]), ("skipped", "130 to 160 a week"))
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: errors, `AttributeError: ... 'plan_launch'`.

- [ ] **Step 3: Implement**

Append to `measurements.py`:

```python
def _find(items: list[dict], item_id: str) -> dict:
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            return item
    raise ValueError(f"no measurement with id {item_id}")


def _days_after(day: str, n: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()


def plan_launch(home: str, item_id: str, launch_date: str, today: str) -> list[dict]:
    _check_date("launch_date", launch_date)
    _check_date("today", today)
    items = load(home)
    item = _find(items, item_id)
    done = [c for c in item.get("checks") or [] if isinstance(c, dict) and c.get("done_at")]
    undone_dues = [_days_after(launch_date, n) for n in CHECK_DAYS[len(done):]]
    item["launch_date"] = launch_date
    item["checks"] = done + [{"due": d, "done_at": None, "value": None, "verdict": None} for d in undone_dues]
    item["updated_at"] = today
    return _write(home, items, f"set launch of {item_id} to {launch_date}")


def plan_check(home: str, item_id: str, due: str, value: str, verdict: str, today: str) -> list[dict]:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    _check_date("due", due)
    _check_date("today", today)
    items = load(home)
    item = _find(items, item_id)
    for check in item.get("checks") or []:
        if isinstance(check, dict) and check.get("due") == due:
            check.update({"done_at": today, "value": value, "verdict": verdict})
            item["stage"] = "after"
            item["updated_at"] = today
            return _write(home, items, f"record the {due} check of {item_id}: {verdict}")
    raise ValueError(f"no check due on {due} for {item_id}")


def plan_skip(home: str, item_id: str, title: str, link: str, kind: str, reason: str, today: str) -> list[dict]:
    if kind not in KINDS:
        raise ValueError(f"work kind must be one of {KINDS}")
    if not reason:
        raise ValueError("a skip needs a reason")
    _check_date("today", today)
    items = load(home)
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            item.update({"stage": "skipped", "skipped_reason": reason, "updated_at": today})
            return _write(home, items, f"skip {item_id}")
    items.append({"id": item_id, "work": {"title": title, "link": link, "kind": kind}, "stage": "skipped",
                  "skipped_reason": reason, "created_at": today, "updated_at": today})
    return _write(home, items, f"skip {item_id}")
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: `OK` (23 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/lib/career/measurements.py plugins/flagrare/lib/career/tests/test_measurements.py
git commit -m "✨ feat(measure-impact): launch dates, checks after launch, and skips"
```

---

### Task 4: What is due today, and the command line

**Files:**
- Modify: `plugins/flagrare/lib/career/measurements.py`
- Test: `plugins/flagrare/lib/career/tests/test_measurements.py`

**Interfaces:**
- Consumes: `load`, `BET_WAIT_DAYS`, `career_state.read_contributions(home) -> list[str]` (lines starting `- `).
- Produces:
  - `due(home: str, today: str) -> dict` with keys `checks_due` (list of `{id, title, due}`), `bets_waiting` (list of `{id, title, since}`), `unmeasured_wins` (list of `{date, link, text}`) and `count` (int);
  - `_log_link(line: str) -> str` (normalized link or `""`);
  - the CLI `main()` with commands `plan|launch|check|skip|due|show`.

- [ ] **Step 1: Write the failing tests**

Append to `test_measurements.py`:

```python
LOG = ".claude/skills/flagrare/career/contributions.log.md"


class Due(unittest.TestCase):
    def test_given_nothing_saved_when_asking_then_nothing_is_due(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(m.due(d, "2026-10-02")["count"], 0)

    def test_given_a_check_past_its_date_when_asking_then_lists_it_and_not_a_future_one(self):
        with tempfile.TemporaryDirectory() as d:
            checks = [{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None},
                      {"due": "2026-11-12", "done_at": None, "value": None, "verdict": None}]
            saved(d, [entry(launch_date="2026-10-01", checks=checks)])
            result = m.due(d, "2026-10-16")
            self.assertEqual(result["checks_due"], [{"id": "acme-reorder", "title": "Reorder button for Acme Pizza", "due": "2026-10-15"}])

    def test_given_a_bet_with_no_launch_after_30_days_when_asking_then_lists_it_as_waiting(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [{**entry(), "created_at": "2026-09-01"}, {**entry(id="fresh"), "created_at": "2026-09-25"}])
            self.assertEqual([b["id"] for b in m.due(d, "2026-10-02")["bets_waiting"]], ["acme-reorder"])

    def test_given_log_entries_when_asking_then_lists_only_those_with_no_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), LOG, "# log\n\n"
                  "- 2026-09-20 | https://tracker.example/T-1 | Shipped the reorder button | behavior: x\n"
                  "- 2026-09-21 | https://chat.example/p1 | Answered Sam on payouts | behavior: y\n"
                  "- 2026-09-22 | https://docs.example/d2). | Wrote the onboarding doc | behavior: z\n")
            saved(d, [entry(), {"id": "d2", "work": {"title": "doc", "link": "https://docs.example/d2", "kind": "log_entry"}, "stage": "skipped", "skipped_reason": "no number possible"}])
            wins = m.due(d, "2026-10-02")["unmeasured_wins"]
            self.assertEqual([w["link"] for w in wins], ["https://chat.example/p1"])

    def test_given_odd_log_lines_when_asking_then_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), LOG, "- 2026-09-20 | Shipped without a link\n-   \n- not | enough\n")
            result = m.due(d, "2026-10-02")
            self.assertIsInstance(result["unmeasured_wins"], list)

    def test_given_a_skipped_entry_with_an_overdue_check_when_asking_then_stays_silent(self):
        with tempfile.TemporaryDirectory() as d:
            saved(d, [entry(stage="skipped", skipped_reason="dropped", checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None}])])
            self.assertEqual(m.due(d, "2026-10-20")["checks_due"], [])
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measurements -q`
Expected: errors, `AttributeError: ... 'due'`.

- [ ] **Step 3: Implement `due`**

Append to `measurements.py`:

```python
LINK_RE = re.compile(r"https?://\S+")


def _log_link(line: str) -> str:
    parts = [p.strip() for p in line[2:].split("|")] if line.startswith("- ") else []
    if len(parts) < 2:
        return ""
    found = LINK_RE.search(parts[1])
    return found.group(0).rstrip(").,;") if found else ""


def due(home: str, today: str) -> dict:
    _check_date("today", today)
    items = [i for i in load(home) if isinstance(i, dict)]
    known_links = {((i.get("work") or {}).get("link") or "").rstrip(").,;") for i in items}
    checks_due, waiting = [], []
    wait_cutoff = (date.fromisoformat(today) - timedelta(days=BET_WAIT_DAYS)).isoformat()
    for item in items:
        if item.get("stage") == "skipped":
            continue
        title = (item.get("work") or {}).get("title", "")
        for check in item.get("checks") or []:
            if isinstance(check, dict) and not check.get("done_at") and check.get("due") and check["due"] <= today:
                checks_due.append({"id": item.get("id"), "title": title, "due": check["due"]})
        created = item.get("created_at") or ""
        if item.get("stage") == "before" and not item.get("launch_date") and created and created <= wait_cutoff:
            waiting.append({"id": item.get("id"), "title": title, "since": created})
    wins = []
    for line in career_state.read_contributions(home):
        link = _log_link(line)
        if link and link not in known_links:
            parts = [p.strip() for p in line[2:].split("|")]
            wins.append({"date": parts[0], "link": link, "text": parts[2] if len(parts) > 2 else ""})
    return {"checks_due": checks_due, "bets_waiting": waiting, "unmeasured_wins": wins,
            "count": len(checks_due) + len(waiting) + len(wins)}
```

- [ ] **Step 4: Add the command line**

Append to `measurements.py`:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only helper for /flagrare:measure-impact.")
    parser.add_argument("command", choices=["plan", "launch", "check", "skip", "due", "show"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--today")
    parser.add_argument("--entry", help="plan: the measurement as a JSON object")
    parser.add_argument("--id")
    parser.add_argument("--launch-date")
    parser.add_argument("--due")
    parser.add_argument("--value", default="")
    parser.add_argument("--verdict")
    parser.add_argument("--title", default="")
    parser.add_argument("--link", default="")
    parser.add_argument("--kind")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    try:
        if args.command == "show":
            result: object = load(args.home)
        elif not args.today:
            parser.error(f"{args.command} needs --today")
        elif args.command == "due":
            result = due(args.home, args.today)
        elif args.command == "plan":
            try:
                entry = json.loads(args.entry or "")
            except json.JSONDecodeError as exc:
                parser.error(f"--entry is not valid JSON: {exc}")
            result = plan_upsert(args.home, entry, args.today)
        elif args.command == "launch":
            result = plan_launch(args.home, args.id or "", args.launch_date or "", args.today)
        elif args.command == "check":
            result = plan_check(args.home, args.id or "", args.due or "", args.value, args.verdict or "", args.today)
        else:
            result = plan_skip(args.home, args.id or "", args.title, args.link, args.kind or "", args.reason, args.today)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests, then try the CLI**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

Run: `cd plugins/flagrare/lib/career && python3 measurements.py due --home "$(mktemp -d)" --today 2026-10-02`
Expected: JSON with `"count": 0`.

Run: `cd plugins/flagrare/lib/career && python3 measurements.py check --home "$(mktemp -d)" --today 2026-10-02 --id x --due 2026-10-01 --verdict great`
Expected: exit code 2 and `verdict must be one of`.

- [ ] **Step 6: Commit**

```bash
git add plugins/flagrare/lib/career/measurements.py plugins/flagrare/lib/career/tests/test_measurements.py
git commit -m "✨ feat(measure-impact): what is due today, from checks, waiting bets and the contributions log"
```

---

### Task 5: The skill, its evals, and the shared docs

**Files:**
- Create: `plugins/flagrare/skills/measure-impact/SKILL.md`
- Create: `plugins/flagrare/skills/measure-impact/evals/evals.json`
- Create: `plugins/flagrare/skills/measure-impact/evals/fixtures/config.json`, `promotion-map.json`, `contributions.log.md`, `measurements.json`
- Modify: `plugins/flagrare/lib/career/STATE.md`, `plugins/flagrare/lib/career/GLOSSARY.md`

**Interfaces:**
- Consumes: the CLI from Task 4 (`measurements.py plan|launch|check|skip|due|show`), `scoring.py context` (promotion map `priorities`), `career_state.py plan`.
- Produces: the skill name `measure-impact` and its arguments contract `<before|after|past> <link or title> [quick|full] [called by /flagrare:<skill>]`, which Milestones 2 and 3 rely on.

- [ ] **Step 1: Write the skill**

Create `plugins/flagrare/skills/measure-impact/SKILL.md`:

````markdown
---
name: measure-impact
description: Measure the impact of a piece of the user's work in a systematic way, at any stage. Before building, it makes an educated guess (a "bet"): a measured baseline, the closest comparable that can be measured, scaled by the right base, a range, a confidence level, and the saved query that will measure it. After launch, it re-runs that same query and gives a verdict (worked, didn't work, can't tell). For work already shipped, it finds the best number still available or says honestly that none exists. Every result is written as action, measured result, impact, for the user's written case and for sharing. Use when the user says "measure impact", "what impact did this have", "how will we know this worked", "set a bet", "success metric", "shipped", "launched", "self-review", "brag", or when another flagrare skill hands off with "called by". Do not use for small fixes with no user-visible change: record a skip instead.
---

# Measure Impact

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook.

> **Plain words.** Use the plain names in `<plugin root>/lib/career/GLOSSARY.md` ("bet", "baseline", "check", "confidence level", "your written case"). The plugin root is two directories above this skill's base directory.

Impact claims without a method go wrong in three ways: targets that are wishes, numbers about the wrong thing, and checks nobody runs after launch. This skill runs the same method every time, saves what it found, and comes back to it.

**It never posts, sends or publishes anything.** It runs read-only queries only. Every write goes through `measurements.py` and the Write tool.

## Library

`python3 <plugin root>/lib/career/measurements.py <command> --home "$HOME" --today <YYYY-MM-DD> ...` prints planned writes as JSON. Apply each `write` action with the Write tool, reading `measurements.json` first if it exists. A refusal (exit code 2) prints the reason: tell the user in plain words and do not work around it. If it says the file is corrupt, stop and show the user the path.

- `plan --entry '<json>'`: save a new measurement, or update one with the same id.
- `launch --id <id> --launch-date <date>`: set the launch date; creates checks 14 and 42 days later.
- `check --id <id> --due <date> --value "<text>" --verdict worked|didnt_work|cant_tell`: record a check.
- `skip --id <id> --title "<work>" --link <link> --kind ticket|tdd|project|log_entry --reason "<why>"`: record a skip.
- `due`: checks past their date, bets with no launch after 30 days, and contributions-log entries with no measurement.
- `show`: everything saved.

The file's shape is in `<plugin root>/lib/career/STATE.md`.

## Stages

Decide the stage from what you were given, or take it from the arguments:

| Given | Stage |
|---|---|
| a ticket, a TDD, a project or proposal not built yet | before |
| something shipped with a launch date, or a check from `due` | after |
| a contributions-log entry or past work with no number | past |

Sizes: **quick** (about 5 minutes; steps 1, 2, 4 and 9) for tickets and log entries; **full** (all steps) for TDDs, projects and written-case entries. When the arguments name no size, use quick for tickets and log entries and full otherwise. Small fixes with no user-visible change get `skip` with the reason, and nothing else.

## The method, every time

1. **The work and its kind of impact:** for users or partners, technical (speed, errors, reliability, cost), business (revenue, orders, cost), or for the team (time saved, fewer interruptions). Often more than one.
2. **The number that shows it.** Prefer a number leadership already watches. When `<plugin root>/lib/career/scoring.py context --home "$HOME"` reports `has_map: true`, read the promotion map's `priorities` (theme, metric, baseline, target, owner team, the user's lever) and connect to one of them first; name the theme.
3. **Where the data lives.** List the connected tools by category and use what exists: source control (git, GitHub), tickets, docs, chat, observability (Datadog, New Relic, Grafana), errors (Sentry), product analytics and the data warehouse (Snowflake, BigQuery, Segment, PostHog). Never assume a tool the session does not have.
4. **The baseline:** today's value, with the exact query or link and the date. Run the query read-only. If it cannot be found, say why and what would get it.
5. **A comparable, when there is no direct baseline:** the closest thing that can be measured (a similar feature, team, market or past launch), scaled by the right base (per booking, venue, order, user or week), never compared as a raw count. Example: reports per 10,000 bookings in one product, applied to the order volume of the other.
6. **The range and the confidence level,** with the reasons it could be higher or lower.
7. **How much is the user's:** `mine` (their own work), `team` (a team effort they were part of), or `contributed` (someone else's, which they helped).
8. **How it will be tracked:** the event, metric or table that will show the change, and whether it exists. If it does not, say what to add.
9. **The sentence.** Before: "We believe [change] will [result], because [evidence]". After and past: "[action], [measured result], leading to [impact]".

## Confidence levels

Every number and every claim about cause carries one:

| Level | Meaning | Wording |
|---|---|---|
| direct | a source states it: a query result, a dashboard value, a written statement | "is", "was", with the source next to it |
| supported | several pieces of evidence agree | "the evidence points to", listing them |
| inferred | a reasonable reading of the context; the reasoning is written out | "likely", "suggests", "is consistent with" |
| speculative | a plausible guess; other explanations fit too | "one possibility is" |
| unknown | searched and not found | "searched X, Y and Z and found nothing" |

Words that claim cause ("because", "fixes", "led to") only appear at direct or supported, with the source right next to them.

## Verdicts after launch

Re-run the saved query, not a new one, so the check reads as old value against new value. Then:

- **worked:** the number moved the way the bet said, inside or above the range.
- **didn't work:** it did not move, or moved the wrong way.
- **can't tell:** too little data, or something else changed at the same time.

"Can't tell" is not a pass. A negative result is reported plainly, never hidden or softened.

## Output

Show the user, in plain words:

1. The stage and size, and what the work is.
2. The number, its baseline (with source) or comparable, the range, the confidence level, and how much is theirs.
3. The sentence.
4. What was saved, and the next date it will come up (the next check, or "when it launches, tell me the date").

Then save with `plan` (or `check` / `skip`). When something launches, ask for the launch date and run `launch`.

**Called by another skill** (`called by /flagrare:<skill>` in the arguments): do the work, save it, and return only the sentence, the number with its source and confidence level, and the id. The calling skill presents it.

## Rules

- Never invent a number. Every number has a source, or a confidence level and its reasoning.
- Read-only queries only, and never save a credential in a query (the script refuses).
- Report negative and unclear results as plainly as good ones.
- Do not measure other people's work, except to say how much of a shared result is the user's.

## Credits

The confidence levels and their wording, finding data by category across connected tools, the old value against new value check with its three verdicts, and saving the check so it can be re-run are adapted from pstack (MIT, by Lauren Tan; Claude Code port by Lucas Faria): the `why`, `figure-it-out` and `prove-it-works` skills.
````

- [ ] **Step 2: Write the eval fixtures**

Create `plugins/flagrare/skills/measure-impact/evals/fixtures/config.json`:

```json
{
  "github_login": "kai-dev",
  "display_name": "Kai",
  "skills": { "impact-scan": { "onboarding_complete": true, "target_level": "senior" } }
}
```

Create `plugins/flagrare/skills/measure-impact/evals/fixtures/promotion-map.json` with only what the skill reads:

```json
{
  "target": { "target_level": { "value": "Senior", "source": "ladder", "checked_at": "2026-10-01", "status": "verified" } },
  "priorities": [
    { "theme": "Merchant trust", "metric": { "value": "Share of merchants unhappy with how they understand payouts", "source": "themes doc", "checked_at": "2026-10-01", "status": "verified" },
      "baseline": { "value": "20%", "source": "themes doc", "checked_at": "2026-10-01", "status": "verified" },
      "owner_team": "Payments", "user_lever": "input" }
  ],
  "sections": {}
}
```

Create `plugins/flagrare/skills/measure-impact/evals/fixtures/contributions.log.md`:

```markdown
# Contributions

- 2026-09-20 | https://tracker.example/T-1 | Shipped the reorder button for Acme Pizza | behavior: team-first
- 2026-09-24 | https://chat.example/p7 | Found that 20% of merchant order emails were held back in a test group, and got it removed | behavior: team-first
```

Create `plugins/flagrare/skills/measure-impact/evals/fixtures/measurements.json`:

```json
[
  { "id": "acme-reorder", "work": { "title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket" },
    "stage": "before", "metric": { "name": "repeat orders per week", "why": "the button exists to bring people back" },
    "source": { "category": "data warehouse", "tool": "warehouse", "query": "select count(*) from orders where repeat = true and week = current_week", "run_at": "2026-09-15" },
    "baseline": { "value": "120 a week", "as_of": "2026-09-15", "confidence": "direct" },
    "bet": { "sentence": "We believe a reorder button will lift repeat orders, because Sam's survey says people retype orders", "range": "130 to 160 a week", "confidence": "inferred" },
    "ownership": "mine", "launch_date": "2026-09-20",
    "checks": [ { "due": "2026-10-04", "done_at": null, "value": null, "verdict": null }, { "due": "2026-11-01", "done_at": null, "value": null, "verdict": null } ],
    "created_at": "2026-09-15", "updated_at": "2026-09-20" }
]
```

- [ ] **Step 3: Write the evals**

Create `plugins/flagrare/skills/measure-impact/evals/evals.json`:

```json
{
  "skill_name": "measure-impact",
  "evals": [
    {
      "id": 0,
      "prompt": "Before I build it: how will we know if the new 'save my usual order' shortcut for Acme Pizza works? Ticket https://tracker.example/T-5. My files are in ~/.claude/skills/flagrare/ (see the fixtures).",
      "expected_output": "Agent treats it as the before stage at quick size, names the kind of impact, picks a number (repeat or faster orders), looks for a baseline in the connected tools and either gives it with its query and date or says it could not be found and how to get it, writes 'We believe ... because ...' with a range and a confidence level, and saves it through measurements.py plan with the Write tool. No number appears without a source or a confidence level.",
      "files": ["evals/fixtures/config.json", "evals/fixtures/measurements.json", "evals/fixtures/contributions.log.md"]
    },
    {
      "id": 1,
      "prompt": "What impact did my Sep 24 contribution have? No data tools are connected in this session.",
      "expected_output": "Agent treats it as the past stage for the 2026-09-24 log entry, uses the number already in the entry (20% of emails held back) as direct with the log as its source, says it cannot measure what changed after the removal because no data tool is reachable, marks that part unknown and names what it would query, writes the action, result, impact sentence without inventing an after number, and offers to save it.",
      "files": ["evals/fixtures/config.json", "evals/fixtures/contributions.log.md", "evals/fixtures/measurements.json"]
    },
    {
      "id": 2,
      "prompt": "The two-week check on the reorder button is due. The same query now returns 124 a week, and a big holiday promotion ran that week.",
      "expected_output": "Agent re-runs or uses the saved query's result, compares 120 to 124 against the bet's 130 to 160 range, and gives the verdict can't tell (or didn't work), explaining the promotion as a confounder, not worked. It records the check with measurements.py check, verdict cant_tell or didnt_work, and does not soften the result.",
      "files": ["evals/fixtures/measurements.json"]
    },
    {
      "id": 3,
      "prompt": "I fixed a typo on the menu page, should I measure it?",
      "expected_output": "Agent says it is a small fix with no user-visible impact worth measuring, records a skip with measurements.py skip and a reason, and does not build a bet.",
      "files": ["evals/fixtures/measurements.json"]
    }
  ]
}
```

- [ ] **Step 4: Document the file in STATE.md**

In `plugins/flagrare/lib/career/STATE.md`, add this section at the end:

````markdown
## measurements.json

Impact measurements, written by `/flagrare:measure-impact` through `measurements.py` (plan-only, like the other scripts). One entry per piece of work measured or skipped:

```json
[{ "id": "stable-slug",
   "work": { "title": "plain words", "link": "<ticket, TDD, PR or log entry>", "kind": "ticket|tdd|project|log_entry" },
   "stage": "before|after|past|skipped", "skipped_reason": "",
   "impact_types": ["partners", "business"],
   "metric": { "name": "...", "why": "...", "priority_theme": "<theme from the map, when any>" },
   "source": { "category": "data warehouse", "tool": "...", "query": "<exact text, no credentials>", "run_at": "2026-10-02" },
   "baseline": { "value": "...", "as_of": "2026-10-02", "confidence": "direct" },
   "comparable": { "what": "...", "base": "per 10,000 bookings", "value": "...", "confidence": "supported" },
   "bet": { "sentence": "We believe ...", "range": "...", "confidence": "inferred" },
   "ownership": "mine|team|contributed",
   "launch_date": null,
   "checks": [{ "due": "2026-10-19", "done_at": null, "value": null, "verdict": "worked|didnt_work|cant_tell" }],
   "result": { "sentence": "", "confidence": "" },
   "created_at": "2026-10-02", "updated_at": "2026-10-02" }]
```

- Confidence levels: `direct`, `supported`, `inferred`, `speculative`, `unknown`. The script refuses anything else, an unknown stage, kind or ownership, dates not written `YYYY-MM-DD`, and a query that looks like it holds a credential.
- `plan` adds an entry or updates the one with the same id, keeping its checks and launch date. `launch` sets the launch date and creates checks 14 and 42 days later; re-launching keeps checks already done and moves only the rest. `check` records a check and moves the entry to `after`. `skip` records a skip with its reason.
- `due` lists undone checks whose date has passed, `before` entries with no launch date 30 days after they were saved, and contributions-log entries whose link matches no measurement. Skipped entries never appear.
- A corrupt file is never overwritten: every command refuses until it is fixed.
````

- [ ] **Step 5: Add the plain names to GLOSSARY.md**

In `plugins/flagrare/lib/career/GLOSSARY.md`, add these rows to the table, after the row for "The bet":

```markdown
| Baseline | baseline, before value | The number today, with where it came from and when it was taken. |
| Check | after check, follow-up | Measuring again with the same query, 2 and 6 weeks after launch, and saying whether the bet worked. |
| Confidence level | confidence, certainty | How sure a number or claim is: direct (a source says it), supported (several sources agree), inferred (a reasonable reading), speculative (a guess), unknown (searched, not found). |
| Win with no number | unmeasured log entry | A contribution in the log that has no measurement yet. |
```

- [ ] **Step 6: Check for em-dashes and run everything**

Run: `grep -rn $'\u2014' plugins/flagrare/skills/measure-impact plugins/flagrare/lib/career/STATE.md plugins/flagrare/lib/career/GLOSSARY.md`
Expected: no output.

Run: `python3 -c "import json;json.load(open('plugins/flagrare/skills/measure-impact/evals/evals.json'));[json.load(open(f'plugins/flagrare/skills/measure-impact/evals/fixtures/{n}')) for n in ('config.json','promotion-map.json','measurements.json')];print('ok')"`
Expected: `ok`.

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add plugins/flagrare/skills/measure-impact plugins/flagrare/lib/career/STATE.md plugins/flagrare/lib/career/GLOSSARY.md
git commit -m "✨ feat(measure-impact): the skill, its evals, and the shared docs"
```

---

### Task 6: Release

**Files:**
- Modify: `plugins/flagrare/.claude-plugin/plugin.json` (via the script), `CHANGELOG.md`

**Interfaces:**
- Consumes: everything above.
- Produces: a tagged release the user can install.

- [ ] **Step 1: Find the newest tag**

Run: `git fetch --tags && git tag --sort=-v:refname | head -1`
Expected: the latest version (at plan time `v1.55.0`). The new version is the next minor after whatever this prints.

- [ ] **Step 2: Bump**

Run: `python3 scripts/bump-version.py <next minor, e.g. 1.56.0>`

- [ ] **Step 3: Write the CHANGELOG entry**

Add at the top of `CHANGELOG.md`, below `# Changelog`, in the file's existing narrative style:

```markdown
## <version>: <date>

Measure what your work changed, before and after you build it.

### New Skills

- **`/flagrare:measure-impact`**: the career skills found work worth doing and logged what you did, but nothing measured what it changed, so most log entries read as activity. Now one skill runs the same method every time:
  - **Before you build:** an educated guess with a measured baseline (or a comparable scaled per booking, order or user), a range, a confidence level, and the exact query saved.
  - **After launch:** the same query re-run at 2 and 6 weeks, with an honest verdict: worked, didn't work, or can't tell.
  - **Past work:** the best number still findable for wins already in your log, or a plain "unknown, searched X and Y".
  - Every result comes out as action, measured result, impact, ready for your written case.
  - Small fixes are skipped and remembered, so you're never asked twice.
- Credits: confidence levels and the old-vs-new check are adapted from pstack (MIT, Lauren Tan; Claude Code port by Lucas Faria).
```

- [ ] **Step 4: Commit, tag, publish, update**

```bash
git add CHANGELOG.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "🔖 release: v<version>"
git tag -a v<version> -m "v<version>"
git push origin main && git push origin v<version>
awk '/^## <version>/{f=1;next}/^## /{f=0}f' CHANGELOG.md > "$TMPDIR/notes.md"
gh release create v<version> --title v<version> --notes-file "$TMPDIR/notes.md"
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

Run the last line with the sandbox disabled (it rewrites `~/.claude/plugins/`).
Expected: "Plugin flagrare updated from <old> to <version>".
