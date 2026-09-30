# Career skills, Milestone 1: `promotion` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan or in anything it produces (repo hook). Check with `python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" <files>`, which must print 0. Do NOT run `scripts/check-no-emdash.py` by hand: it reads hook JSON from stdin and hangs.

**Goal:** Ship `/flagrare:promotion`, the skill that builds a sourced promotion map (target, company process and calendar, rubric gap, org and who knows your work, plan), plus the shared `career/` state layer that the other three career skills will use.

**Architecture:** The deterministic parts live in a small stdlib-only Python library at `plugins/flagrare/lib/career/`: a state resolver, a map validator, and a deadline calculator. They are pure functions with CLIs that print JSON and never write files. The skill's `SKILL.md` drives the research and interview, runs the CLIs, and writes every file with the Write tool, since a sandboxed Bash cannot write under `~/.claude/skills`. Senior-scan is untouched in this milestone.

**Tech Stack:** Markdown skills (Claude Code plugin), Python 3 stdlib (`json`, `datetime`, `pathlib`, `unittest`), `evals/evals.json` (repo precedent: `plugins/flagrare/skills/debug-hunt/evals/evals.json`).

**Spec:** `docs/plans/2026-09-30-career-skills-design.md`

## Global Constraints

- No em-dashes in any file (repo hook). Verify with `python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))"`.
- Python: stdlib only, `from __future__ import annotations`, runs on the system `python3` (3.14 here). No pip installs.
- Tests: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`, run from the repo root.
- The library never writes files. Every write under `~/.claude/skills/flagrare/` happens through the Write tool, driven by `SKILL.md`.
- Shared state folder: `~/.claude/skills/flagrare/career/`. Legacy folder: `~/.claude/skills/flagrare/senior-scan/`.
- Every map fact carries `source`, `checked_at` (ISO date) and `status`, one of `verified`, `unverified` or `inferred`. Conflicting sources are stored as `alternatives`, never collapsed.
- A section older than 90 days counts as stale.
- The deadline calculator defaults to 14 days for peer quotes, 14 for drafting and 14 for gap-closing, and a 14-day comfortable buffer. Holiday dead windows are inputs; no dates are hardcoded.
- Skills reference the library by a path relative to the plugin root, never an absolute path: `<plugin root>/lib/career/<script>.py`. The plugin root is two directories above the skill's base directory, which the harness prints on invocation.
- **The skill never posts, sends or publishes anything.** The map and board stay local.
- Commits go directly to `main`, gitmoji plus conventional style (`✨ feat(promotion): ...`), with **no attribution lines**.

## Review Focus

1. **Log divergence:** a user who keeps running senior-scan after `career/` exists. Reading contributions must return the union of both logs, with no lost entries (pinned in Task 1).
2. **Deadline already passed, or falling inside a holiday window:** the calculator returns `state: "past"` or skips dead days. It never returns a nonsense or negative window (pinned in Task 3).
3. **Partial map after an interrupted first run:** the validator treats absent sections as "not yet", not as errors (pinned in Task 2).
4. **Brand-new user** with neither folder: the resolver plans only "create career/", with no copies and no crash (pinned in Task 1).
5. **Migration planned twice:** idempotent, and never plans to overwrite a `career/` file with less content (pinned in Task 1).

---

## File Structure

```
plugins/flagrare/lib/career/
  career_state.py      # paths, config fallback, contributions union, migration planner (pure, no writes)
  map_schema.py        # validate map JSON, list conflicts, missing and stale sections
  deadlines.py         # manager-conversation window from a packet deadline
  tests/
    __init__.py
    test_career_state.py
    test_map_schema.py
    test_deadlines.py
plugins/flagrare/skills/promotion/
  SKILL.md             # the skill
  reference/
    map-schema.md      # promotion-map.json shape and fact rules
    map-template.md    # promotion-map.md fixed sections
  evals/
    evals.json         # 4 behavior cases
README.md              # add a promotion paragraph
CHANGELOG.md           # 1.43.0 entry
plugins/flagrare/.claude-plugin/plugin.json  # version bump via scripts/bump-version.py
```

---

### Task 1: State resolver (`career_state.py`)

**Files:**
- Create: `plugins/flagrare/lib/career/career_state.py`
- Create: `plugins/flagrare/lib/career/tests/__init__.py` (empty)
- Test: `plugins/flagrare/lib/career/tests/test_career_state.py`

**Interfaces:**
- Produces (used by `SKILL.md` now, and by impact-scan, opportunity-scan and career later):
  - `paths(home: str) -> dict[str, str]` with keys `career_dir, legacy_dir, config, map_md, map_json, initiatives, log, scan_state, flags, voice`.
  - `read_contributions(home: str) -> list[str]`: entry lines (starting with `- `), legacy first, then career-only extras, deduplicated.
  - `plan_migration(home: str) -> list[dict]`: actions `{"action": "mkdir"|"write", "path": str, "content": str|None, "reason": str}`.
  - `skill_config(config: dict, name: str) -> dict` (the `impact-scan` key falls back to `senior-scan`).
  - `board_dir(config: dict) -> str | None` (`skills.career.board.dir`, falling back to `skills["senior-scan"].board.dir`).
  - CLI: `python3 career_state.py paths|contributions|plan --home <dir>`, printing JSON.

- [ ] **Step 1: Write the failing tests**

```python
# plugins/flagrare/lib/career/tests/test_career_state.py
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import career_state as cs  # noqa: E402

LEGACY = ".claude/skills/flagrare/senior-scan"
CAREER = ".claude/skills/flagrare/career"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


class ReadContributions(unittest.TestCase):
    def test_given_only_legacy_log_when_reading_then_returns_its_entries(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# Senior scan contributions\n\n- a\n- b\n")
            self.assertEqual(cs.read_contributions(str(home)), ["- a", "- b"])

    def test_given_both_logs_diverged_when_reading_then_returns_union_without_loss(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n- b\n- c\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a\n- d\n")
            self.assertEqual(cs.read_contributions(str(home)), ["- a", "- b", "- c", "- d"])

    def test_given_no_logs_when_reading_then_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(cs.read_contributions(d), [])


class PlanMigration(unittest.TestCase):
    def test_given_brand_new_user_when_planning_then_only_creates_career_dir(self):
        with tempfile.TemporaryDirectory() as d:
            actions = cs.plan_migration(d)
            self.assertEqual([a["action"] for a in actions], ["mkdir"])

    def test_given_legacy_only_when_planning_then_copies_everything_and_adds_pointer(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n")
            write(home, f"{LEGACY}/state.json", '{"last_run": "2026-09-30"}')
            write(home, f"{LEGACY}/voice.md", "short sentences")
            actions = cs.plan_migration(str(home))
            written = {Path(a["path"]).name: a["content"] for a in actions if a["action"] == "write"}
            self.assertIn("- a", written["contributions.log.md"])
            self.assertEqual(written["scan-state.json"], '{"last_run": "2026-09-30"}')
            self.assertEqual(written["voice.md"], "short sentences")
            self.assertIn("career", written["MOVED.md"])

    def test_given_migration_already_applied_when_planning_again_then_plans_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n")
            for a in cs.plan_migration(str(home)):
                if a["action"] == "mkdir":
                    Path(a["path"]).mkdir(parents=True, exist_ok=True)
                else:
                    Path(a["path"]).write_text(a["content"])
            self.assertEqual(cs.plan_migration(str(home)), [])

    def test_given_career_log_has_extra_entries_when_planning_then_never_drops_them(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/contributions.log.md", "# h\n\n- a\n- b\n")
            write(home, f"{CAREER}/contributions.log.md", "# h\n\n- a\n- z\n")
            log_writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            for entry in ("- a", "- b", "- z"):
                self.assertIn(entry, log_writes[0]["content"])

    def test_given_existing_career_state_when_planning_then_does_not_overwrite_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", '{"old": true}')
            write(home, f"{CAREER}/scan-state.json", '{"new": true}')
            paths = [a["path"] for a in cs.plan_migration(str(home))]
            self.assertFalse(any(p.endswith("scan-state.json") for p in paths))


class Config(unittest.TestCase):
    def test_given_only_legacy_key_when_reading_impact_scan_config_then_falls_back(self):
        cfg = {"skills": {"senior-scan": {"domains": ["x"]}}}
        self.assertEqual(cs.skill_config(cfg, "impact-scan"), {"domains": ["x"]})

    def test_given_new_key_when_reading_impact_scan_config_then_prefers_it(self):
        cfg = {"skills": {"senior-scan": {"a": 1}, "impact-scan": {"b": 2}}}
        self.assertEqual(cs.skill_config(cfg, "impact-scan"), {"b": 2})

    def test_given_legacy_board_dir_when_resolving_then_falls_back(self):
        cfg = {"skills": {"senior-scan": {"board": {"dir": "~/b"}}}}
        self.assertEqual(cs.board_dir(cfg), "~/b")

    def test_given_no_board_when_resolving_then_none(self):
        self.assertIsNone(cs.board_dir({}))


class Cli(unittest.TestCase):
    def test_given_home_when_running_paths_then_prints_json_with_career_dir(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run(
                [sys.executable, str(Path(cs.__file__)), "paths", "--home", d],
                capture_output=True, text=True, check=True,
            ).stdout
            self.assertTrue(json.loads(out)["career_dir"].endswith("flagrare/career"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'career_state'`

- [ ] **Step 3: Write the implementation**

```python
# plugins/flagrare/lib/career/career_state.py
"""Shared state for the flagrare career skills.

Pure functions: this module never writes files. Skills apply the actions it
plans with the Write tool, because a sandboxed shell cannot write under
~/.claude/skills.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CAREER_REL = Path(".claude/skills/flagrare/career")
LEGACY_REL = Path(".claude/skills/flagrare/senior-scan")
CONFIG_REL = Path(".claude/skills/flagrare/config.json")
LOG_HEADER = "# Career contributions"
MOVED_NOTE = (
    "# Mirrored\n\n"
    "`~/.claude/skills/flagrare/career/` mirrors these files for the career skills.\n"
    "Senior-scan still writes here until impact-scan replaces it; nothing here is deleted.\n"
)


def paths(home: str) -> dict[str, str]:
    root = Path(home)
    career = root / CAREER_REL
    return {
        "career_dir": str(career),
        "legacy_dir": str(root / LEGACY_REL),
        "config": str(root / CONFIG_REL),
        "map_md": str(career / "promotion-map.md"),
        "map_json": str(career / "promotion-map.json"),
        "initiatives": str(career / "initiatives.json"),
        "log": str(career / "contributions.log.md"),
        "scan_state": str(career / "scan-state.json"),
        "flags": str(career / "flags.json"),
        "voice": str(career / "voice.md"),
    }


def _read(path: Path) -> str | None:
    return path.read_text() if path.is_file() else None


def _entries(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.rstrip() for line in text.splitlines() if line.startswith("- ")]


def _header(text: str | None) -> str | None:
    if not text:
        return None
    for line in text.splitlines():
        if line.startswith("# "):
            return line
    return None


def read_contributions(home: str) -> list[str]:
    p = paths(home)
    legacy = _entries(_read(Path(p["legacy_dir"]) / "contributions.log.md"))
    career = _entries(_read(Path(p["log"])))
    merged: list[str] = []
    seen: set[str] = set()
    for line in legacy + career:
        if line not in seen:
            seen.add(line)
            merged.append(line)
    return merged


def plan_migration(home: str) -> list[dict]:
    p = paths(home)
    career = Path(p["career_dir"])
    legacy = Path(p["legacy_dir"])
    actions: list[dict] = []
    if not career.is_dir():
        actions.append({"action": "mkdir", "path": str(career), "content": None, "reason": "create shared career state folder"})

    legacy_log = _read(legacy / "contributions.log.md")
    career_log = _read(Path(p["log"]))
    if legacy_log is not None:
        merged = read_contributions(home)
        if merged != _entries(career_log):
            header = _header(career_log) or _header(legacy_log) or LOG_HEADER
            content = header + "\n\n" + "\n".join(merged) + "\n"
            actions.append({"action": "write", "path": p["log"], "content": content, "reason": "union of legacy and career logs, nothing dropped"})

    for legacy_name, target_key in (("state.json", "scan_state"), ("voice.md", "voice")):
        source = _read(legacy / legacy_name)
        if source is not None and not Path(p[target_key]).is_file():
            actions.append({"action": "write", "path": p[target_key], "content": source, "reason": f"copy {legacy_name} from senior-scan"})

    if legacy.is_dir() and not (legacy / "MOVED.md").is_file():
        actions.append({"action": "write", "path": str(legacy / "MOVED.md"), "content": MOVED_NOTE, "reason": "pointer to the new career folder"})
    return actions


def skill_config(config: dict, name: str) -> dict:
    skills = (config or {}).get("skills", {})
    if name in skills:
        return skills[name]
    if name == "impact-scan":
        return skills.get("senior-scan", {})
    return {}


def board_dir(config: dict) -> str | None:
    skills = (config or {}).get("skills", {})
    for key in ("career", "senior-scan"):
        board = skills.get(key, {}).get("board", {})
        if board.get("dir"):
            return board["dir"]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only state helper for the flagrare career skills.")
    parser.add_argument("command", choices=["paths", "contributions", "plan"])
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    if args.command == "paths":
        result: object = paths(args.home)
    elif args.command == "contributions":
        result = read_contributions(args.home)
    else:
        result = plan_migration(args.home)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 13 tests.

- [ ] **Step 5: Commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/lib/career/career_state.py plugins/flagrare/lib/career/tests/test_career_state.py
git add plugins/flagrare/lib/career
git commit -m "✨ feat(promotion): shared career state resolver with safe senior-scan migration planning"
```

---

### Task 2: Map validator (`map_schema.py`)

**Files:**
- Create: `plugins/flagrare/lib/career/map_schema.py`
- Test: `plugins/flagrare/lib/career/tests/test_map_schema.py`

**Interfaces:**
- Produces:
  - `SECTIONS: list[str] = ["target", "process", "calendar", "rubric", "org", "people", "precedent", "packet_readiness", "manager_questions"]`
  - `validate(m: dict) -> list[str]`: error strings; absent sections are not errors.
  - `conflicts(m: dict) -> list[str]`: dotted paths of facts that carry `alternatives`.
  - `missing_sections(m: dict) -> list[str]`
  - `stale_sections(m: dict, today: date, days: int = 90) -> list[str]`: present sections whose `sections.<name>.checked_at` is older than `days` or absent. Career's scheduler will call this in Milestone 4.
  - CLI: `python3 map_schema.py check <map.json> --today YYYY-MM-DD`, printing `{"errors": [...], "missing": [...], "stale": [...], "conflicts": [...]}`.
- A **fact** is any dict with a `status` key. It is either `{"value", "source", "checked_at", "status"}` or `{"alternatives": [fact, ...], "status"}`.

- [ ] **Step 1: Write the failing tests**

```python
# plugins/flagrare/lib/career/tests/test_map_schema.py
from __future__ import annotations
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import map_schema as ms  # noqa: E402

GOOD_FACT = {"value": "Senior", "source": "https://x", "checked_at": "2026-09-30", "status": "verified"}


class Validate(unittest.TestCase):
    def test_given_partial_map_after_phase_two_when_validating_then_no_errors_and_rest_missing(self):
        m = {
            "target": {"target_level": GOOD_FACT},
            "rubric": {"rows": []},
            "sections": {"target": {"checked_at": "2026-09-30"}, "rubric": {"checked_at": "2026-09-30"}},
        }
        self.assertEqual(ms.validate(m), [])
        self.assertIn("org", ms.missing_sections(m))
        self.assertNotIn("target", ms.missing_sections(m))

    def test_given_fact_without_source_when_validating_then_reports_its_path(self):
        m = {"target": {"target_level": {"value": "Senior", "checked_at": "2026-09-30", "status": "verified"}}}
        errors = ms.validate(m)
        self.assertTrue(any("target.target_level" in e and "source" in e for e in errors))

    def test_given_unknown_status_when_validating_then_reports_it(self):
        m = {"target": {"target_level": {**GOOD_FACT, "status": "probably"}}}
        self.assertTrue(any("status" in e for e in ms.validate(m)))


class Conflicts(unittest.TestCase):
    def test_given_two_sources_disagree_when_listing_conflicts_then_both_kept_and_path_reported(self):
        fact = {
            "status": "unverified",
            "alternatives": [
                {"value": "Alex", "source": "notion", "checked_at": "2026-09-30", "status": "unverified"},
                {"value": "Sam", "source": "miro", "checked_at": "2026-09-30", "status": "unverified"},
            ],
        }
        m = {"org": {"n2_manager_reports_to": fact}}
        self.assertEqual(ms.validate(m), [])
        self.assertEqual(ms.conflicts(m), ["org.n2_manager_reports_to"])


class Stale(unittest.TestCase):
    def test_given_section_checked_over_90_days_ago_when_checking_then_stale(self):
        m = {"org": {}, "sections": {"org": {"checked_at": "2026-05-01"}}}
        self.assertEqual(ms.stale_sections(m, date(2026, 9, 30)), ["org"])

    def test_given_present_section_without_checked_at_when_checking_then_stale(self):
        self.assertEqual(ms.stale_sections({"people": []}, date(2026, 9, 30)), ["people"])

    def test_given_absent_section_when_checking_then_not_stale(self):
        self.assertEqual(ms.stale_sections({}, date(2026, 9, 30)), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'map_schema'`

- [ ] **Step 3: Write the implementation**

```python
# plugins/flagrare/lib/career/map_schema.py
"""Checks for promotion-map.json. Read-only; reports, never fixes."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

SECTIONS = ["target", "process", "calendar", "rubric", "org", "people", "precedent", "packet_readiness", "manager_questions"]
STATUSES = {"verified", "unverified", "inferred"}


def _walk(node: object, path: str):
    if isinstance(node, dict):
        if "status" in node:
            yield path, node
            for i, alt in enumerate(node.get("alternatives", []) or []):
                yield from _walk(alt, f"{path}.alternatives[{i}]")
            return
        for key, value in node.items():
            yield from _walk(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


def validate(m: dict) -> list[str]:
    errors: list[str] = []
    for section in SECTIONS:
        if section not in m:
            continue
        for path, fact in _walk(m[section], section):
            if fact.get("status") not in STATUSES:
                errors.append(f"{path}: status must be one of {sorted(STATUSES)}")
            if "alternatives" in fact:
                if len(fact["alternatives"]) < 2:
                    errors.append(f"{path}: alternatives needs at least two entries")
                continue
            for field in ("value", "source", "checked_at"):
                if field not in fact:
                    errors.append(f"{path}: missing {field}")
    return errors


def conflicts(m: dict) -> list[str]:
    found: list[str] = []
    for section in SECTIONS:
        if section in m:
            found += [path for path, fact in _walk(m[section], section) if "alternatives" in fact]
    return found


def missing_sections(m: dict) -> list[str]:
    return [s for s in SECTIONS if s not in m]


def stale_sections(m: dict, today: date, days: int = 90) -> list[str]:
    meta = m.get("sections", {})
    stale: list[str] = []
    for section in SECTIONS:
        if section not in m:
            continue
        checked = meta.get(section, {}).get("checked_at")
        if not checked or (today - date.fromisoformat(checked)).days > days:
            stale.append(section)
    return stale


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a promotion-map.json file.")
    parser.add_argument("command", choices=["check"])
    parser.add_argument("map_path")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()
    m = json.loads(Path(args.map_path).read_text())
    today = date.fromisoformat(args.today)
    print(json.dumps({
        "errors": validate(m),
        "missing": missing_sections(m),
        "stale": stale_sections(m, today),
        "conflicts": conflicts(m),
    }, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 20 tests in total.

- [ ] **Step 5: Commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/lib/career/map_schema.py plugins/flagrare/lib/career/tests/test_map_schema.py
git add plugins/flagrare/lib/career
git commit -m "✨ feat(promotion): promotion map validator with conflicts, missing and stale sections"
```

---

### Task 3: Deadline calculator (`deadlines.py`)

**Files:**
- Create: `plugins/flagrare/lib/career/deadlines.py`
- Test: `plugins/flagrare/lib/career/tests/test_deadlines.py`

**Interfaces:**
- Produces:
  - `manager_conversation_window(packet_deadline: date, today: date, dead_windows: list[tuple[date, date]] = (), published: bool = False, peer_quote_days: int = 14, draft_days: int = 14, gap_days: int = 14, buffer_days: int = 14) -> dict`
  - The return value is `{"absolute_by": iso, "comfortable_by": iso, "status": "verified"|"inferred", "state": "ok"|"tight"|"past", "assumptions": {...}}`.
  - Days inside `dead_windows` (inclusive) are skipped when counting back.
  - CLI: `python3 deadlines.py --deadline YYYY-MM-DD --today YYYY-MM-DD [--dead START:END ...] [--published]`, printing JSON.

- [ ] **Step 1: Write the failing tests**

```python
# plugins/flagrare/lib/career/tests/test_deadlines.py
from __future__ import annotations
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deadlines as dl  # noqa: E402

HOLIDAYS = [(date(2026, 12, 20), date(2027, 1, 2))]


class Window(unittest.TestCase):
    def test_given_last_years_calendar_and_holidays_when_computing_then_late_oct_and_mid_nov(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30), HOLIDAYS)
        self.assertEqual(w["absolute_by"], "2026-11-12")
        self.assertEqual(w["comfortable_by"], "2026-10-29")
        self.assertEqual(w["state"], "ok")

    def test_given_unpublished_calendar_when_computing_then_marked_inferred(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30), HOLIDAYS)
        self.assertEqual(w["status"], "inferred")

    def test_given_published_calendar_when_computing_then_marked_verified(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30), HOLIDAYS, published=True)
        self.assertEqual(w["status"], "verified")

    def test_given_today_between_comfortable_and_absolute_when_computing_then_tight(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 11, 5), HOLIDAYS)
        self.assertEqual(w["state"], "tight")

    def test_given_today_after_absolute_when_computing_then_past(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 12, 1), HOLIDAYS)
        self.assertEqual(w["state"], "past")

    def test_given_deadline_inside_holidays_when_computing_then_skips_dead_days(self):
        w = dl.manager_conversation_window(date(2026, 12, 25), date(2026, 9, 1), HOLIDAYS)
        self.assertEqual(w["absolute_by"], "2026-11-08")

    def test_given_no_dead_windows_when_computing_then_counts_plain_days(self):
        w = dl.manager_conversation_window(date(2027, 1, 7), date(2026, 9, 30))
        self.assertEqual(w["absolute_by"], "2026-11-26")
        self.assertEqual(w["comfortable_by"], "2026-11-12")


if __name__ == "__main__":
    unittest.main()
```

Expected dates, computed with the same algorithm before writing this plan (counting back one day at a time, skipping dead days):
- From 2027-01-07, 42 counted days: Jan 6 to Jan 3 is 4 days, Dec 20 to Jan 2 is skipped, and Dec 19 back to Nov 12 is 38 days. Total 42, so `absolute_by` is 2026-11-12. Then 14 more days gives 2026-10-29.
- From 2026-12-25 (inside the window): Dec 24 to Dec 20 is skipped, and the 42 counted days run from Dec 19 back to 2026-11-08.
- With no dead windows: 42 days before 2027-01-07 is 2026-11-26, and 14 before that is 2026-11-12.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'deadlines'`

- [ ] **Step 3: Write the implementation**

```python
# plugins/flagrare/lib/career/deadlines.py
"""When to talk to your manager, worked back from the packet deadline."""
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta


def _dead(day: date, windows) -> bool:
    return any(start <= day <= end for start, end in windows)


def _back(start: date, days: int, windows) -> date:
    current = start
    remaining = days
    while remaining > 0:
        current -= timedelta(days=1)
        if not _dead(current, windows):
            remaining -= 1
    return current


def manager_conversation_window(
    packet_deadline: date,
    today: date,
    dead_windows=(),
    published: bool = False,
    peer_quote_days: int = 14,
    draft_days: int = 14,
    gap_days: int = 14,
    buffer_days: int = 14,
) -> dict:
    windows = list(dead_windows)
    absolute = _back(packet_deadline, peer_quote_days + draft_days + gap_days, windows)
    comfortable = _back(absolute, buffer_days, windows)
    if today > absolute:
        state = "past"
    elif today > comfortable:
        state = "tight"
    else:
        state = "ok"
    return {
        "absolute_by": absolute.isoformat(),
        "comfortable_by": comfortable.isoformat(),
        "status": "verified" if published else "inferred",
        "state": state,
        "assumptions": {
            "packet_deadline": packet_deadline.isoformat(),
            "dead_windows": [[s.isoformat(), e.isoformat()] for s, e in windows],
            "peer_quote_days": peer_quote_days,
            "draft_days": draft_days,
            "gap_days": gap_days,
            "buffer_days": buffer_days,
        },
    }


def _window(text: str) -> tuple[date, date]:
    start, end = text.split(":")
    return date.fromisoformat(start), date.fromisoformat(end)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manager-conversation window for a promotion cycle.")
    parser.add_argument("--deadline", required=True)
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--dead", action="append", default=[], help="START:END, inclusive, repeatable")
    parser.add_argument("--published", action="store_true")
    args = parser.parse_args()
    result = manager_conversation_window(
        date.fromisoformat(args.deadline),
        date.fromisoformat(args.today),
        [_window(w) for w in args.dead],
        published=args.published,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 27 tests in total.

- [ ] **Step 5: Commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/lib/career/deadlines.py plugins/flagrare/lib/career/tests/test_deadlines.py
git add plugins/flagrare/lib/career
git commit -m "✨ feat(promotion): manager-conversation deadline calculator that skips holiday dead time"
```

---

### Task 4: Reference files (map schema and human template)

**Files:**
- Create: `plugins/flagrare/skills/promotion/reference/map-schema.md`
- Create: `plugins/flagrare/skills/promotion/reference/map-template.md`

**Interfaces:**
- Consumes: the fact shape and `SECTIONS` from Task 2.
- Produces: the two files `SKILL.md` points to in Task 5.

- [ ] **Step 1: Write `map-schema.md`**

````markdown
# promotion-map.json

Written only by `/flagrare:promotion`. Read by impact-scan, opportunity-scan and career. Check it with `python3 <plugin root>/lib/career/map_schema.py check <path>`.

## Facts

Every fact is an object with a `status`:

- Single source: `{"value": ..., "source": "<link or quoted location>", "checked_at": "YYYY-MM-DD", "status": "verified|unverified|inferred"}`
- Sources disagree: `{"status": "unverified", "alternatives": [fact, fact, ...]}`. Keep every alternative, and show all of them to the user.

Statuses:
- `verified`: read in the raw source, quoted verbatim.
- `unverified`: seen only in a summary, a search snippet, or secondhand.
- `inferred`: derived by reasoning (for example, who sits in calibration, or deadlines from last year's calendar).

## Sections

Absent sections mean "not researched yet", not an error.

```json
{
  "target": {
    "current_level": {}, "target_level": {}, "track": {}, "cycle": {},
    "why": "user's words", "more_of": ["..."], "less_of": ["..."],
    "level_is_terminal": {}, "current_level_band": {}
  },
  "process": {
    "steps": [{}], "who_initiates": {}, "decision_makers": {}, "calibration_room": {},
    "packet_template": {"sections": ["..."], "length": {}, "peer_feedback": {}},
    "decision_process": {"artifact": {}, "usual_driver": {}}
  },
  "calendar": {
    "cycle_name": "...", "packet_deadline": {}, "calibration": {}, "effective": {},
    "dead_windows": [["YYYY-MM-DD", "YYYY-MM-DD"]],
    "manager_conversation": {"comfortable_by": "...", "absolute_by": "...", "status": "inferred", "state": "ok|tight|past"}
  },
  "rubric": {
    "artifact": {}, "prose_mismatches": [{}],
    "rows": [{"id": "scope.proactive-discovery", "area": "Scope & Impact",
              "current_text": {}, "target_text": {},
              "status": "done|partial|not_started", "evidence": ["log line or link"]}]
  },
  "org": {"chain": [{}], "options": [{}], "changes": [{}]},
  "people": [{"name": "...", "role": {}, "relation": "...", "seen_your_work": true,
              "evidence": ["link"], "confirmed_by_user": true}],
  "precedent": {"tier": "announcements|deep", "caveat": "announcements are narratives, not audits", "cases": [{}]},
  "packet_readiness": [{"section": "...", "state": "strong|thin|empty", "evidence_rows": ["rubric row id"]}],
  "manager_questions": ["..."],
  "sections": {"target": {"checked_at": "YYYY-MM-DD", "sources": ["..."]}}
}
```

Rubric row ids are `<area>.<short-slug>`, lowercase with hyphens, and stay stable across refreshes. Impact-scan tags contributions with these ids.
````

- [ ] **Step 2: Write `map-template.md`**

````markdown
# Promotion map: <name>, <current level> to <target level>

Last full check: <date>. Sources and statuses for every fact are in `promotion-map.json`. Anything marked (inferred) or (unverified) needs confirming before you rely on it.

## 1. Where you're going
- **Target:** <level>, <track>, aiming at <cycle>.
- **Why:** <the user's words>. **More of:** <...>. **Less of:** <...>.
- **Is the target level terminal here?** <yes/no + quote + link>
- **Expected time at your current level:** <band + link>
- **What the "why" means for the plan:** <one or two sentences>

## 2. How promotion works here
<Process steps, who initiates, who decides, who sits in calibration (inferred, with the source sentence), the packet template, and how product decisions get made (the decision document and who usually drives it). Each line has its link.>

## 3. The calendar
| Step | Date | Status |
|---|---|---|
<packet deadline, calibration, effective date>

**Talk to your manager:** comfortable by <date>, absolute by <date> (<status>, <state>).

## 4. The gap
| Area | Your level | Target level | Status | Evidence |
|---|---|---|---|---|
<one row per rubric row>

<Any mismatch between the rubric file and prose about it.>

## 5. The org
<Your chain, who sits above each landing option, and upcoming changes. Conflicts shown with both sources.>

## 6. Who knows your work
| Person | Role | How they know your work | Seen your work? |
|---|---|---|---|
<confirmed people>

**Still needs to see your work:** <names>

## 7. What got people promoted here
<Precedent cases. Announcements are narratives, not audits.>

## 8. Packet readiness
| Packet section | State | Evidence |
|---|---|---|

## 9. Questions to bring to your manager
<numbered list>
````

- [ ] **Step 3: Verify and commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/skills/promotion/reference/*.md
git add plugins/flagrare/skills/promotion/reference
git commit -m "✨ feat(promotion): promotion map schema and human template references"
```

---

### Task 5: `promotion/SKILL.md`

**Files:**
- Create: `plugins/flagrare/skills/promotion/SKILL.md`

**Interfaces:**
- Consumes: the CLIs from Tasks 1-3 and the references from Task 4.
- Produces: the `/flagrare:promotion` skill. Map files go to `career/`, and `packet` mode drafts the packet.

- [ ] **Step 1: Write the skill**

````markdown
---
name: promotion
description: Build and maintain a sourced promotion map for the user's next level. It interviews the user about their target (level, track, cycle, and why), researches how promotions actually work at their company (process, calendar, packet template, the rubric managers rate against), maps the org and who has first-hand knowledge of the user's work, and computes when to talk to their manager. Every fact carries a source and a verified/unverified/inferred status, and conflicting sources are shown, not resolved silently. Writes ~/.claude/skills/flagrare/career/promotion-map.md and .json, which impact-scan, opportunity-scan and career read. Use when the user says "promotion", "promo plan", "how do promotions work here", "when should I talk to my manager about promotion", "who should see my work", "am I ready for senior", "build my promotion map", or "promotion packet" (packet mode). Also trigger when the user asks about career strategy, sponsors, or calibration at their company.
---

# Promotion

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

A promotion is decided in a room the user isn't in, from a written case, by people who mostly don't know them, on a calendar set months ahead. This skill makes those facts visible early: where the user wants to go and why, how the company actually decides, what the rubric asks for, who has first-hand knowledge of their work, and when the key conversations must happen.

It writes a **promotion map**: `promotion-map.md` for the user to read and bring to a 1:1, and `promotion-map.json` with the same facts for the other career skills. The map is local and private. **This skill never posts, sends, or publishes anything.**

## Library

The plugin ships helper scripts at `<plugin root>/lib/career/`. The plugin root is two directories above this skill's base directory. They only read and print JSON; this skill writes every file with the Write tool, because a sandboxed shell cannot write under `~/.claude/skills`.

- `career_state.py paths|contributions|plan --home "$HOME"`: file locations, the contributions log (union of old and new locations), and the migration plan.
- `map_schema.py check <map.json> --today YYYY-MM-DD`: errors, missing sections, stale sections (over 90 days), conflicts.
- `deadlines.py --deadline YYYY-MM-DD --today YYYY-MM-DD --dead START:END [--published]`: when to talk to the manager.

The map's shape is in `reference/map-schema.md`, and the markdown layout is in `reference/map-template.md`.

## 1. Load state (every run)

1. Run `career_state.py plan`. Apply each action with the Write tool (`mkdir` means write any file into the folder, starting with the map). **Never delete anything.**
2. Read `~/.claude/skills/flagrare/config.json` (top-level identity keys, the `skills.promotion` block) and the existing map, if any.
3. No map means a **first run**. A map means a **refresh** (section 4), unless the user asks for `packet` mode (section 5).

## 2. Rules for every fact

- **Source, date, status.** Every fact gets a link or quoted location, the date you checked it, and a status: `verified` (read and quoted in the raw source), `unverified` (a summary, snippet or secondhand), or `inferred` (your reasoning).
- **Quote verbatim from the raw source.** Summarizing fetch tools paraphrase. When a quote will be relied on, re-read the raw page (for example the page's JSON or HTML) and confirm the exact words.
- **Show conflicts, never pick silently.** When two sources disagree (an org chart vs a squad directory, a process page vs the ladder file), store both as `alternatives` and tell the user.
- **"Nothing found" is a valid result.** If a step finds nothing, add a concrete question to `manager_questions` instead of guessing. Many companies have no written process.
- **People facts are sensitive.** Only read the user's own interactions. Record who has first-hand context on the user's work, never a ranking of how useful people are.
- **Ask for consent before using the browser** on HR portals or internal sites.

## 3. First run

Tell the user up front: the first run is long, often an hour or more, and it saves after each phase, so it can be stopped and resumed.

### Phase 1: Target, process and calendar
1. **Interview first, before any research.** Ask one question at a time:
   1. Current level and target level.
   2. Track: individual contributor or manager.
   3. Which cycle they're aiming at (propose one once the calendar is known).
   4. **Why** they want it, what work they want **more of**, and what they want **less of**.
2. **Look up two facts about the target level:** is it terminal at this company (no expectation of promotion beyond it), and what's the expected time band at the current level? Quote both.
3. **Say what the "why" changes.** A terminal target plus a "peace of mind" why makes the target the finish line. A "money" or "scope" why means planning past it. Write this into the map's section 1.
4. **Find the process, calendar and packet template** in every connected source: wiki, docs, chat announcements, meeting notes, the HR portal (with consent). Also find **how product decisions get made**: the decision document and who usually drives it. Opportunity-scan needs this.
5. Save the map (JSON and markdown) with the `target`, `process`, `calendar` and `sections` entries filled in.

### Phase 2: Rubric gap
1. **Find the artifact managers rate against** (a ladder spreadsheet, a check-in workbook), not prose written about it. Ask the user whether their manager uses a check-in workbook. If prose and artifact disagree, use the artifact and record the mismatch in `rubric.prose_mismatches`.
2. Build one `rubric.rows` entry per behavior: the current-level text, the target-level text, and a stable id (`<area>.<short-slug>`).
3. Mark each row `done`, `partial` or `not_started`, with evidence from `career_state.py contributions`, the user's reviews and work, and prior review notes the user shares.
4. Save.

### Phase 3: Org and who knows your work
1. **Org:** the user's chain, who sits above each team they might land on, and upcoming changes (departures, new leaders, reorgs from meeting notes and announcements). Every person gets a source and a status.
2. **Who knows your work, evidence first, then the user:**
   - Propose people from the user's own interactions (reviews given and received, shared threads, shared meetings), each with evidence links.
   - Ask the user to confirm and correct, and to add what no tool can see, like a former manager or a hackathon team.
   - Set `seen_your_work` and `confirmed_by_user`.
3. **Who sits in calibration:** infer it from the process document, quote the sentence, and mark it `inferred`. List the people in the room who haven't seen the user's work.
4. **Precedent:** read recent promotion announcements for what got credited, and write "announcements are narratives, not audits" in the map. Offer the **deep tier** only if the user asks: cross-checking in code, docs and tickets who actually originated the work. It is expensive and off by default.
5. Save.

### Phase 4: Plan
1. **Deadlines:** run `deadlines.py` with the packet deadline. Use this cycle's date if published; otherwise last year's, marked `inferred`. Ask the user which holiday or vacation windows are dead time where they are, and pass them as `--dead`. Record "comfortable by X, absolute by Y" with its status and state. If the state is `past`, say so plainly and name the next cycle.
2. **Packet readiness:** for each template section, mark `strong`, `thin` or `empty` from the rubric rows and evidence.
3. **Manager questions:** everything still unknown, plus the readiness question ("is <cycle> realistic, and what's missing?").
4. Run `map_schema.py check`. Fix any errors, then save.
5. Show the user a short summary: the target, the two conversation dates, open rubric gaps, who still needs to see their work, and the questions for their manager. Point to `promotion-map.md`.

## 4. Refresh

1. Run `map_schema.py check`, and read `career/flags.json` if it exists (other skills write staleness signals there, such as a reorg, a departure, or a calendar being published).
2. Re-research only the stale or flagged sections. Keep every other section as it is.
3. Ask the user "anything changed?", covering target, manager, team, and people who have seen their work.
4. Update `checked_at` for each re-checked section, clear the flags you handled, and save.

## 5. Packet mode (`/flagrare:promotion packet`)

When the packet deadline approaches, or the user asks:
1. Load the map. Use `/flagrare:brag-doc` over the evidence window to gather material.
2. Draft the packet in the company's template, from `process.packet_template`: the header fields, then 2-3 projects (role, estimate vs actual, complexity), mentorship and team building, technical craft, and a list of people to ask for peer quotes.
3. Write each project as action, then measurable result, then impact. Tell a story, not a list of tickets, and name the target-level rubric line each project demonstrates.
4. Save it as `career/packet-draft.md` for the user to edit. **Never submit it anywhere.**
````

- [ ] **Step 2: Verify**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/skills/promotion/SKILL.md
python3 plugins/flagrare/lib/career/career_state.py paths --home "$HOME" >/dev/null && echo cli-ok
```
Expected: `0`, then `cli-ok`.

- [ ] **Step 3: Commit**

```bash
git add plugins/flagrare/skills/promotion/SKILL.md
git commit -m "✨ feat(promotion): promotion skill with sourced four-phase map, refresh and packet mode"
```

---

### Task 6: Evals

**Files:**
- Create: `plugins/flagrare/skills/promotion/evals/evals.json`

- [ ] **Step 1: Write the eval cases**

```json
{
  "skill_name": "promotion",
  "evals": [
    {
      "id": 0,
      "prompt": "I want to get promoted. Can you build my promotion map?",
      "expected_output": "Agent says the first run is long and saves after each phase, then interviews before researching: asks current and target level, track (IC or manager), target cycle, and why plus what work they want more of and less of, one question at a time.",
      "files": []
    },
    {
      "id": 1,
      "prompt": "HR hasn't published this year's review calendar. Last year packets were due January 7 and we lose Dec 20 to Jan 2 to holidays. When do I need to talk to my manager?",
      "expected_output": "Agent runs the deadline calculator (or reasons the same way), gives a comfortable date and an absolute date, marks both inferred because the calendar is unpublished, and says to re-check when HR publishes.",
      "files": []
    },
    {
      "id": 2,
      "prompt": "The squad directory in Notion says my future manager reports to Alex, but the Miro org chart shows them reporting to Sam. Which is right?",
      "expected_output": "Agent does not pick one silently: records both as alternatives with their sources and status unverified, shows both to the user, and suggests how to confirm (for example, asking the manager).",
      "files": []
    },
    {
      "id": 3,
      "prompt": "Update my promotion map with how promotions are decided at my company.",
      "expected_output": "When no written process is found in the connected sources, the agent says so, adds concrete questions to manager_questions (who decides, when, what the packet looks like) instead of inventing a process, and saves the partial map.",
      "files": []
    }
  ]
}
```

- [ ] **Step 2: Validate the JSON and commit**

```bash
python3 -c "import json;json.load(open('plugins/flagrare/skills/promotion/evals/evals.json'));print('ok')"
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/skills/promotion/evals/evals.json
git add plugins/flagrare/skills/promotion/evals
git commit -m "✨ feat(promotion): eval cases for interview-first, inferred deadlines, conflicts and nothing-found"
```

---

### Task 7: README, CHANGELOG and release 1.43.0

**Files:**
- Modify: `README.md` (the Review section, right before the paragraph starting "`/flagrare:senior-scan` scans your org's communication surfaces")
- Modify: `CHANGELOG.md` (new top section)
- Modify: `plugins/flagrare/.claude-plugin/plugin.json` (through the script only)

- [ ] **Step 1: Add the README paragraph**

Insert before the senior-scan paragraph:

```markdown
`/flagrare:promotion` builds a promotion map for your next level and keeps it current. It interviews you first (target level, track, cycle, and why, plus what work you want more and less of), then researches how promotion actually works at your company: the process, the calendar, the packet template, and the rubric file managers rate against, preferring that file over prose about it. It maps the org and who has first-hand knowledge of your work, confirming each person with you, and computes when to talk to your manager ("comfortable by, absolute by", skipping holiday dead time). Every fact carries a source and a verified, unverified or inferred status, and conflicting sources are shown side by side. The map lives locally in `~/.claude/skills/flagrare/career/`, where the other career skills read it, and `packet` mode drafts your promotion packet in the company's format. It never posts anything.
```

- [ ] **Step 2: Run the tests one last time**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: all pass.

- [ ] **Step 3: Commit the README**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" README.md
git add README.md
git commit -m "📝 docs(readme): add promotion to the skill catalog"
```

- [ ] **Step 4: Bump the version and add the CHANGELOG entry**

```bash
python3 scripts/bump-version.py 1.43.0
python3 -c "import json;print(json.load(open('plugins/flagrare/.claude-plugin/plugin.json'))['version'])"
```
Expected: `1.43.0`.

Insert at the top of `CHANGELOG.md`, directly under `# Changelog` and its blank line:

```markdown
## 1.43.0: 2026-09-30

A promotion is decided in a room you're not in; now you can see the room.

### New Skills

- **`/flagrare:promotion`, a sourced map of your next level**: senior-scan found threads to weigh in on, but the work that mattered most in a promotion case was never automated. Field-tested the hard way in one long session that grew into a full day of manual research: the org chart from two sources that disagreed, the promotion process from a wiki page, an HR portal and chat announcements, the rubric spreadsheet that contradicted the prose summarizing it, a calendar worked back from last year's dates, and which managers had actually seen the user's work (the most important of them, a former manager, known only to the user). The skill turns that day into four phases that save as they go: an interview first (target, track, cycle, and the why that changes the plan, like a level being terminal), then process and calendar, the rubric gap against the file managers really use, the org and a "who knows your work" list built from evidence and confirmed by the user, and a plan with a mechanically computed "talk to your manager by" window that skips holiday dead time. Every fact carries a source and a verified, unverified or inferred status; conflicting sources are kept side by side; "nothing found" becomes a question for the manager instead of a guess. It writes `promotion-map.md` and `.json` to a new shared `~/.claude/skills/flagrare/career/` folder, the first piece of a career skill family (impact-scan, opportunity-scan and a coordinator follow), and `packet` mode drafts the promotion packet in the company's format. A small stdlib library (`lib/career/`) holds the tested parts: a state resolver that plans a no-loss migration from senior-scan, a map validator, and the deadline calculator.

```

- [ ] **Step 5: Commit the release, tag, push and publish**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" CHANGELOG.md
git diff CHANGELOG.md | python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))"
git add CHANGELOG.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "🔖 release: v1.43.0"
git tag -a v1.43.0 -m "release v1.43.0" HEAD
git push origin main
git push origin v1.43.0
awk '/^## 1.43.0/{f=1;next} /^## 1.42.0/{f=0} f' CHANGELOG.md > "$TMPDIR/rel.md"
gh release create v1.43.0 --title v1.43.0 --notes-file "$TMPDIR/rel.md" --verify-tag
```
Expected: the second check prints 0. The first may count em-dashes that already existed in older entries. The release URL prints at the end.


- [ ] **Step 6: Verify the installed plugin can find the library**

After `/flagrare:update` (run with the sandbox disabled, per the update skill):

```bash
ls ~/.claude/plugins/cache/flagrare-skills/flagrare/1.43.0/lib/career/
python3 ~/.claude/plugins/cache/flagrare-skills/flagrare/1.43.0/lib/career/career_state.py paths --home "$HOME"
```
Expected: the three scripts are listed, and the paths JSON prints with `career_dir` ending in `flagrare/career`.

---

## Self-review notes

- **Spec coverage (M1 scope):**
  - Shared load-state: Task 1 and SKILL section 1.
  - Map JSON and markdown: Tasks 2, 4 and 5.
  - Four phases, saving after each: Task 5.
  - Fact rules and conflicts: Tasks 2 and 5.
  - Terminal level and time band: Task 5, Phase 1.
  - The "why" changes the plan: Task 5.
  - Rubric artifact over prose: Task 5, Phase 2.
  - Evidence-first people list: Task 5, Phase 3.
  - Inferred calibration room: Task 5, Phase 3.
  - Two-tier precedent: Task 5, Phase 3.
  - Mechanical deadlines: Tasks 3 and 5.
  - "Nothing found" becomes a manager question: Tasks 5 and 6.
  - Refresh from flags and stale sections: Tasks 2 and 5.
  - Packet mode: Task 5.
  - Local only, never posts: Task 5.
  - Release: Task 7.
  - Acceptance tests 1 (no loss), 4 (inferred dates), 7 (conflicts) and 8 (partial map) are pinned by unit tests.
- **Deferred to later milestones:** the impact-scan rename, the stub, the impact-timeline path fix, and the board move (M2); opportunity-scan (M3); career and the board panel (M4).
- **Log divergence:** handled by the union in `read_contributions` and `plan_migration`, so the M1 to M2 transition cannot lose entries.
