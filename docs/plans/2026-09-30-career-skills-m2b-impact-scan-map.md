# Career skills, Milestone 2b: map-aware impact-scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan or anything it produces (repo hook). Check with `python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" <files>`, which must print 0. Never run `scripts/check-no-emdash.py` by hand.

**Goal:** Make `/flagrare:impact-scan` use the promotion map: score Stretch against the map's open rubric rows and Audience against people who haven't seen the user's work, raise staleness flags for the map, hand problems that keep coming back to `initiatives.json`, and tag log entries with the rubric row. Without a map it behaves exactly like 1.44.0. Ships as 1.45.0.

**Architecture:** The library supplies inputs and plans writes; the model judges. A new `scoring.py context` lists the open rows, unseen people and the config fallback. `career_state.py` gains `flag` and `candidate`, which print the full new `flags.json` or `initiatives.json` for the skill to write with the Write tool. Which row an item moves and whether two sightings are the same problem stay model judgments, bounded by rules in the skill text (pick from `open_rows` only; a new evidence link is a new sighting).

**Tech Stack:** Markdown skills, Python 3 stdlib, `unittest`, `evals/evals.json` (precedent: `skills/debug-hunt/evals/evals.json`).

**Spec:** `docs/plans/2026-09-30-career-skills-design.md`, Milestone 2 (the behavior half). Carried-over decisions: the rubric-row tag is the additive `| row: <id>` log field; the `behavior:` text stays so the board's coverage panel keeps working until Milestone 4. Deferred to Milestone 4: the "all answering, nothing owned" warning, the board's title and coverage panel rework, a packet-readiness helper.

## Global Constraints

- No em-dashes in any file. Verify with the command above.
- Python stdlib only, `from __future__ import annotations`, system `python3`.
- Tests: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v` from the repo root. Count: the 53 existing tests plus 13 new, 66 in total (if an earlier fix round added tests, expect that many more).
- Library scripts never write under `~/.claude/skills/`; they print planned file content for the skill to write with the Write tool (Read first when the file exists).
- Without a promotion map, impact-scan's scoring, digest and log format are unchanged from 1.44.0.
- Row ids are code-like: never in digest table cells; in the item block, `data.json` (`rubric_rows`) and the log's `| row:` field only.
- Every name in fixtures and evals is invented (the repo is public).
- Commits direct to `main`, gitmoji plus conventional, no attribution lines. Release commit and tag stay local until the user approves publishing.

## Review Focus

1. **No map (the common case today):** `scoring.py context` must return `has_map: false` with the config fallback, reading `skills["impact-scan"]` or the legacy `skills["senior-scan"]` block (Task 2).
2. **An escalating thread must not count as a recurrence:** the same evidence link twice leaves `seen_count` unchanged (Task 1).
3. **Reworded flags:** the same section with the same source is not flagged twice (Task 1).
4. **Unknown section names** are rejected, never written to `flags.json` (Task 1).
5. **A partial map** (no rubric yet): `open_rows` is empty and the skill falls back to configured behaviors (Tasks 2 and 4).

---

## File Structure

```
plugins/flagrare/lib/career/
  career_state.py           # modify: plan_flag, plan_candidate, CLI flag/candidate (Task 1)
  scoring.py                # create: open_rows, unseen_people, context, CLI (Task 2)
  STATE.md                  # modify: handed_off status, flag and candidate rules (Task 3)
  tests/test_career_state.py  # modify (Task 1)
  tests/test_scoring.py       # create (Task 2)
plugins/flagrare/skills/impact-scan/
  SKILL.md                  # rewrite: map-aware scoring, flags, hand-off, row tag (Task 4)
  evals/evals.json          # create (Task 4)
  evals/fixtures/promotion-map.json  # create (Task 4)
README.md, CHANGELOG.md, plugins/flagrare/.claude-plugin/plugin.json  # Task 5
```

---

### Task 1: Flag and candidate planners

**Files:**
- Modify: `plugins/flagrare/lib/career/career_state.py`
- Modify: `plugins/flagrare/lib/career/tests/test_career_state.py`

**Interfaces:**
- Produces:
  - `plan_flag(home, section, reason, source, today) -> list[action]`. It raises `ValueError` for a section outside `map_schema.SECTIONS`. It returns `[]` when a flag for that section already has the same reason or the same non-empty source.
  - `plan_candidate(home, item_id, title, evidence, today) -> list[action]`:
    - It adds `{id, title, evidence, seen_count: 1, first_seen, last_seen, status: "candidate"}` for a new id.
    - For an existing id with a new evidence link, it appends the link, increments `seen_count`, sets `last_seen` and keeps `status`.
    - For an evidence link it already has, it returns `[]`.
  - CLI: `career_state.py flag --home H --section S --reason R --source L --today D` and `career_state.py candidate --home H --id I --title T --evidence L --today D`, printing the action list as JSON. A bad section is an argparse error (exit 2).

- [ ] **Step 1: Write the failing tests**

Insert these classes directly above `class Config(unittest.TestCase):` in `tests/test_career_state.py`:

```python
class Flags(unittest.TestCase):
    def test_given_no_flags_when_flagging_then_writes_one_flag(self):
        with tempfile.TemporaryDirectory() as d:
            [a] = cs.plan_flag(d, "org", "a new team lead was announced", "https://example.com/x", "2026-10-01")
            self.assertEqual(json.loads(a["content"]), [{"section": "org", "reason": "a new team lead was announced", "source": "https://example.com/x", "raised_at": "2026-10-01"}])

    def test_given_same_flag_already_raised_when_flagging_then_plans_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/flags.json", json.dumps([{"section": "org", "reason": "r", "source": "", "raised_at": "2026-09-30"}]))
            self.assertEqual(cs.plan_flag(str(home), "org", "r", "", "2026-10-01"), [])

    def test_given_unknown_section_when_flagging_then_rejects_it(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                cs.plan_flag(d, "gossip", "r", "", "2026-10-01")


class FlagsBySource(unittest.TestCase):
    def test_given_same_section_and_source_reworded_when_flagging_then_plans_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/flags.json", json.dumps([{"section": "org", "reason": "a lead is leaving", "source": "https://example.com/a", "raised_at": "2026-09-30"}]))
            self.assertEqual(cs.plan_flag(str(home), "org", "the team lead is moving on", "https://example.com/a", "2026-10-01"), [])


class Candidates(unittest.TestCase):
    def test_given_same_evidence_link_again_when_recording_then_nothing_changes(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", json.dumps([{"id": "p", "title": "t", "evidence": ["https://example.com/1"], "seen_count": 1, "first_seen": "2026-10-01", "last_seen": "2026-10-01", "status": "candidate"}]))
            self.assertEqual(cs.plan_candidate(str(home), "p", "t", "https://example.com/1", "2026-10-02"), [])

    def test_given_first_sighting_when_recording_then_adds_candidate_seen_once(self):
        with tempfile.TemporaryDirectory() as d:
            [a] = cs.plan_candidate(d, "partner-emails-missing", "Partners miss order emails", "https://example.com/1", "2026-10-01")
            [item] = json.loads(a["content"])
            self.assertEqual((item["seen_count"], item["status"], item["evidence"]), (1, "candidate", ["https://example.com/1"]))

    def test_given_second_sighting_when_recording_then_bumps_count_and_adds_new_evidence_once(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            first = cs.plan_candidate(str(home), "p", "t", "https://example.com/1", "2026-10-01")[0]
            Path(first["path"]).parent.mkdir(parents=True, exist_ok=True)
            Path(first["path"]).write_text(first["content"])
            [a] = cs.plan_candidate(str(home), "p", "t", "https://example.com/2", "2026-10-03")
            [item] = json.loads(a["content"])
            self.assertEqual(item["seen_count"], 2)
            self.assertEqual(item["evidence"], ["https://example.com/1", "https://example.com/2"])
            self.assertEqual((item["first_seen"], item["last_seen"]), ("2026-10-01", "2026-10-03"))

    def test_given_active_initiative_when_seen_again_then_status_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/initiatives.json", json.dumps([{"id": "p", "title": "t", "evidence": [], "seen_count": 3, "first_seen": "2026-09-01", "last_seen": "2026-09-20", "status": "active"}]))
            [a] = cs.plan_candidate(str(home), "p", "t", "https://example.com/3", "2026-10-01")
            self.assertEqual(json.loads(a["content"])[0]["status"], "active")


```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `AttributeError: module 'career_state' has no attribute 'plan_flag'`.

- [ ] **Step 3: Implement**

In `career_state.py`, add these functions directly above `def main() -> None:`:

```python
def _load_list(path: Path) -> list:
    text = _read(path)
    if text is None:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def plan_flag(home: str, section: str, reason: str, source: str, today: str) -> list[dict]:
    """Plan flags.json with one more staleness flag. A flag for the same section with the same reason or the same source is not added twice."""
    from map_schema import SECTIONS
    if section not in SECTIONS:
        raise ValueError(f"section must be one of {SECTIONS}")
    path = Path(paths(home)["flags"])
    flags = _load_list(path)
    for f in flags:
        if isinstance(f, dict) and f.get("section") == section and (f.get("reason") == reason or (source and f.get("source") == source)):
            return []
    flags.append({"section": section, "reason": reason, "source": source, "raised_at": today})
    return [{"action": "write", "path": str(path), "content": json.dumps(flags, indent=2, ensure_ascii=False) + "\n", "reason": f"flag {section} as possibly stale"}]


def plan_candidate(home: str, item_id: str, title: str, evidence: str, today: str) -> list[dict]:
    """Plan initiatives.json with one sighting of a problem: add it, or, for a new evidence link, bump seen_count and add the link. The same link again changes nothing."""
    path = Path(paths(home)["initiatives"])
    items = _load_list(path)
    for item in items:
        if isinstance(item, dict) and item.get("id") == item_id:
            links = item.setdefault("evidence", [])
            if not evidence or evidence in links:
                return []
            links.append(evidence)
            item["seen_count"] = int(item.get("seen_count", 1)) + 1
            item["last_seen"] = today
            break
    else:
        items.append({"id": item_id, "title": title, "evidence": [evidence] if evidence else [], "seen_count": 1,
                      "first_seen": today, "last_seen": today, "status": "candidate"})
    return [{"action": "write", "path": str(path), "content": json.dumps(items, indent=2, ensure_ascii=False) + "\n", "reason": f"record a sighting of {item_id}"}]
```

and replace `main` (currently):

```python
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
```

with:

```python
def main() -> None:
    parser = argparse.ArgumentParser(description="Plan-only state helper for the flagrare career skills.")
    parser.add_argument("command", choices=["paths", "contributions", "plan", "flag", "candidate"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--section")
    parser.add_argument("--reason")
    parser.add_argument("--source", default="")
    parser.add_argument("--id")
    parser.add_argument("--title")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--today")
    args = parser.parse_args()
    if args.command == "paths":
        result: object = paths(args.home)
    elif args.command == "contributions":
        result = read_contributions(args.home)
    elif args.command == "plan":
        result = plan_migration(args.home)
    elif args.command == "flag":
        if not (args.section and args.reason and args.today):
            parser.error("flag needs --section, --reason and --today")
        try:
            result = plan_flag(args.home, args.section, args.reason, args.source, args.today)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        if not (args.id and args.title and args.today):
            parser.error("candidate needs --id, --title and --today")
        result = plan_candidate(args.home, args.id, args.title, args.evidence, args.today)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

- [ ] **Step 4: Run to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 61 tests (53 plus 8).

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/lib/career
git commit -m "✨ feat(impact-scan): plan staleness flags and recurring-problem candidates"
```

---

### Task 2: Scoring inputs

**Files:**
- Create: `plugins/flagrare/lib/career/scoring.py`
- Test: `plugins/flagrare/lib/career/tests/test_scoring.py`

**Interfaces:**
- Consumes: `career_state.paths`, `career_state.skill_config`.
- Produces:
  - `open_rows(map) -> [{id, area, target_text}]`, the rows whose status is not `done`. A `target_text` fact is flattened to its value.
  - `unseen_people(map) -> [name]`, the people with `seen_your_work` false.
  - `context(home) -> {has_map, open_rows, unseen_people, fallback: {target_behaviors, audience}}`.
  - CLI: `python3 scoring.py context --home H`.

- [ ] **Step 1: Write the failing test** `tests/test_scoring.py`:

```python
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scoring  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
FACT = {"value": "x", "source": "https://example.com", "checked_at": "2026-09-30", "status": "verified"}
MAP = {
    "rubric": {"rows": [
        {"id": "scope.proactive-discovery", "area": "Scope & Impact", "status": "partial",
         "target_text": {**FACT, "value": "Proactively discovers and solves problems"}},
        {"id": "craft.code-quality", "area": "Technical Craft", "status": "done", "target_text": FACT},
    ]},
    "people": [
        {"name": "Sam Rivera", "seen_your_work": True},
        {"name": "Alex Chen", "seen_your_work": False},
    ],
}


def write(home: Path, rel: str, data: object) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data))


class OpenRows(unittest.TestCase):
    def test_given_rows_when_listing_then_only_not_done_rows_with_plain_target_text(self):
        self.assertEqual(scoring.open_rows(MAP), [
            {"id": "scope.proactive-discovery", "area": "Scope & Impact", "target_text": "Proactively discovers and solves problems"}])

    def test_given_map_without_rubric_when_listing_then_empty(self):
        self.assertEqual(scoring.open_rows({"target": {}}), [])


class UnseenPeople(unittest.TestCase):
    def test_given_people_when_listing_then_only_those_who_have_not_seen_the_work(self):
        self.assertEqual(scoring.unseen_people(MAP), ["Alex Chen"])


class Context(unittest.TestCase):
    def test_given_no_map_when_building_context_then_fallback_from_legacy_config(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, ".claude/skills/flagrare/config.json", {"skills": {"senior-scan": {"target_behaviors": ["unblocking others"], "audience": ["a manager"]}}})
            ctx = scoring.context(str(home))
            self.assertFalse(ctx["has_map"])
            self.assertEqual(ctx["fallback"], {"target_behaviors": ["unblocking others"], "audience": ["a manager"]})

    def test_given_map_when_building_context_then_lists_open_rows_and_unseen_people(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/promotion-map.json", MAP)
            ctx = scoring.context(str(home))
            self.assertTrue(ctx["has_map"])
            self.assertEqual([r["id"] for r in ctx["open_rows"]], ["scope.proactive-discovery"])
            self.assertEqual(ctx["unseen_people"], ["Alex Chen"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scoring'`.

- [ ] **Step 3: Write `plugins/flagrare/lib/career/scoring.py`**

```python
"""Inputs for impact-scan's Stretch and Audience axes. Read-only.

The model still judges which open rubric row an item closes and who will see
it; this module only lists the choices, from the promotion map when there is
one, or from the scan's own config when there isn't.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import career_state


def open_rows(m: dict) -> list[dict]:
    """Rubric rows not yet done, as {id, area, target_text}. Empty when the map has no rubric."""
    rows = (m.get("rubric") or {}).get("rows") or []
    result = []
    for row in rows:
        if not isinstance(row, dict) or row.get("status") == "done" or not row.get("id"):
            continue
        target = row.get("target_text")
        if isinstance(target, dict):
            target = target.get("value")
        result.append({"id": row["id"], "area": row.get("area", ""), "target_text": target or ""})
    return result


def unseen_people(m: dict) -> list[str]:
    """Names of people in the map who have not seen the user's work."""
    people = m.get("people") or []
    return [p["name"] for p in people if isinstance(p, dict) and p.get("name") and p.get("seen_your_work") is False]


def context(home: str) -> dict:
    """What impact-scan scores against: the map's open rows and unseen people, plus the config fallback."""
    p = career_state.paths(home)
    try:
        config = json.loads(Path(p["config"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        config = {}
    scan = career_state.skill_config(config, "impact-scan")
    fallback = {"target_behaviors": scan.get("target_behaviors", []), "audience": scan.get("audience", [])}
    try:
        m = json.loads(Path(p["map_json"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        m = None
    if not isinstance(m, dict):
        return {"has_map": False, "open_rows": [], "unseen_people": [], "fallback": fallback}
    return {"has_map": True, "open_rows": open_rows(m), "unseen_people": unseen_people(m), "fallback": fallback}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scoring inputs for impact-scan.")
    parser.add_argument("command", choices=["context"])
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    print(json.dumps(context(args.home), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 66 tests (53 plus 13).

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/lib/career
git commit -m "✨ feat(impact-scan): scoring inputs from the promotion map with a config fallback"
```

---

### Task 3: STATE.md rules

**Files:** Modify `plugins/flagrare/lib/career/STATE.md`

- [ ] **Step 1: Replace the whole file with this content**

````markdown
# Career state files

Shared by `/flagrare:promotion`, `/flagrare:impact-scan` and the career skills that follow. They live in `~/.claude/skills/flagrare/career/`, outside the plugin tree so they survive updates. Skills write them with the Write tool (a sandboxed shell cannot write there); the scripts in this folder only read and plan. `career_state.py plan` brings over and merges anything still in the old `~/.claude/skills/flagrare/senior-scan/` folder and never deletes it.

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

Work the user could own. Impact-scan records problem-type items through `career_state.py candidate`, once per scan run: a new evidence link adds a sighting (`seen_count` goes up), a link already recorded changes nothing, so the same thread continuing never counts twice. At `seen_count` 2 or more impact-scan hands the problem off instead of drafting. `/flagrare:opportunity-scan` ranks the candidates. At most one item is `active`.

```json
[{ "id": "stable-slug", "title": "plain words", "evidence": ["<link>"], "seen_count": 2,
   "first_seen": "2026-09-25", "last_seen": "2026-09-30", "status": "candidate|proposed|active|done|dropped" }]
```
````

The changes from the current file are:
- `handed_off` is added to the scan-state status list.
- The flags paragraph gains its dedupe rule.
- The initiatives paragraph gains its sighting rules.

- [ ] **Step 2: Verify and commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/lib/career/STATE.md
git add plugins/flagrare/lib/career/STATE.md
git commit -m "📝 docs(career): flag, candidate and hand-off rules in the state reference"
```

---

### Task 4: Map-aware impact-scan skill, evals and fixture

**Files:**
- Rewrite: `plugins/flagrare/skills/impact-scan/SKILL.md`
- Create: `plugins/flagrare/skills/impact-scan/evals/evals.json`
- Create: `plugins/flagrare/skills/impact-scan/evals/fixtures/promotion-map.json`

The eval `files` field points at the fixture. The repo precedent only shows `files: []`, so whether the eval runner loads the path is unverified; the fixture is there for graders and humans to read.

- [ ] **Step 1: Write the new `SKILL.md`** (complete file, starting with `---` on line 1)

````markdown
---
name: impact-scan
description: Scan the org's communication surfaces (chat like Slack or Teams, open PRs, RFC docs and design docs, ticket threads, whichever MCPs are connected) for high-leverage discussions the user should weigh in on, decisions still being formed, people stuck or circling, questions squarely inside the user's domains, cross-team changes touching systems they own or depend on. Built for engineers working toward promotion, it hunts opportunities to operate at the next level (influence beyond assigned work), ranks them by leverage and credibility, drafts replies in the user's own voice for approval, and logs posted contributions as promotion evidence that /flagrare:brag-doc can later consume. Use whenever the user says "impact scan", "senior scan", "promo scan", "what needs my attention", "where should I weigh in", "anything I should jump into", "scan slack", "scan PRs", "catch me up on what's happening", or any variant of "where can I have the most impact today", even when the skill isn't named. Also trigger when the user talks about wanting more visibility, more scope, or operating above their level.
---

# Impact Scan

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

Promotions lag behavior: you operate at the next level first, and the title follows. This skill hunts the openings where that operating can happen, decisions being shaped, people stuck, questions only this user can answer well, cross-team work touching their systems, and turns them into a ranked digest with ready-to-approve drafts.

The failure mode it must never enable is performative commenting. Shallow opinions dropped in ten visible threads read as noise, not seniority, and actively hurt a promotion case. The bar for surfacing an item: **would this user's contribution change the outcome, and do they have specific knowledge or context that gives them standing?** If either answer is no, the item dies, no matter how visible the thread is. Two substantive contributions beat ten drive-bys.

## Surfaces

The scan runs over **surfaces**: the places where decisions form and people get stuck. Three kinds, in rough order of how often they matter:

- **Chat** (Slack, Microsoft Teams, Discord, Google Chat): fast-moving threads, short decision windows.
- **Code review** (GitHub via MCP or `gh`, GitLab, Bitbucket): open PRs and their review threads.
- **Docs and tickets** (Confluence, Notion, Google Docs, Jira, Linear): often the highest-leverage surface of all. An RFC or design doc in its comment period is literally a decision being formed with an explicit window, exactly what the Timing axis rewards.

Which surfaces this user scans is decided at onboarding from the MCPs actually connected in the session, not hardcoded. Slack and GitHub are the reference implementations with detailed sweep instructions below; any other readable surface runs the generic sweep. At run time, skip any configured surface whose MCP is missing from the session and say so in the digest header; if no surface is reachable, stop and tell the user what to connect.

The scan is **read-only**. Sweep agents must never post, react, comment, or approve anything, and neither may the main flow without the explicit approval gate below.

## Setup and state (every run)

Config lives in the shared **`~/.claude/skills/flagrare/config.json`**: skill-agnostic keys (GitHub login, display name, repo scope) at the top level, impact-scan keys under `skills["impact-scan"]`. This skill was called senior-scan: when `skills["impact-scan"]` is missing, read `skills["senior-scan"]` instead, and write any changes back under `skills["impact-scan"]`. The first time you write that block, copy the whole senior-scan block into `skills["impact-scan"]` and then apply the change, so nothing is lost; leave the senior-scan block in place. Mutable files live in **`~/.claude/skills/flagrare/career/`** (`scan-state.json`, `contributions.log.md`, `voice.md`), shared with the other career skills and outside the plugin tree so they survive plugin updates. Their shapes are in `<plugin root>/lib/career/STATE.md`, where the plugin root is two directories above this skill's base directory. The user's **board** (a local HTML dashboard of open items and the evidence log, see workflow step 7) lives wherever `skills.career.board.dir` points, falling back to `skills["senior-scan"].board.dir`.

Write these files (and `config.json`) with the Write tool, never from Bash: a sandboxed Bash cannot write under `~/.claude/skills`, and a failed state write silently breaks dedupe across runs. Reading them from Bash is fine; expand `~` explicitly as `$HOME`.

**Load state first, every run.** Run `python3 <plugin root>/lib/career/career_state.py plan --home "$HOME"` and apply each `write` action with the Write tool, reading the target first if it exists (the Write tool will not overwrite a file it has not read). This brings over, or merges in, anything still in the old `senior-scan/` folder: the contributions log keeps every entry, the scan state keeps every seen item. A `mkdir` action needs no separate step. **Never delete anything.**

If `onboarding_complete` is not `true` in the impact-scan block (or the senior-scan block it falls back to), run onboarding. Reuse any top-level keys another flagrare skill already collected (ask only for what's missing), and only write the `skills["impact-scan"]` block (plus `skills.career.board`) and missing top-level keys; leave other skills' blocks untouched.

### Onboarding

The interview is half discovery, half confirmation: propose from real data wherever possible so the user is confirming lists, not composing them from memory.

1. **Identity.** GitHub login (detect via `gh api user --jq '.login'` or the GitHub MCP `get_me`, confirm) and repo scope (`org:<name>`, `user:<login>`, or explicit `owner/repo` list). Chat handle: look the user up with the chat MCP's user search, confirm the match.
2. **Career target.** Ask current level and target level, then which next-level behaviors to hunt for. Offer defaults by transition and let the user edit or paste their company ladder's actual language:
   - toward **senior**: influence beyond assigned tickets, unblocking others, owning technical decisions in their domain, raising the quality bar
   - toward **staff**: cross-team leverage, setting direction, connecting efforts that don't know about each other, derisking big decisions early
   The chosen behaviors become the definition of the Stretch axis (see Scoring), so they should be concrete. Once the user has a promotion map (`/flagrare:promotion`), its open rubric rows replace these behaviors for scoring; the config list stays as the fallback.
3. **Domains of real standing.** Spawn a discovery agent over the user's recent GitHub activity (authored PRs, reviews given, comment threads) to propose the areas where they demonstrably know things: systems, failure modes, conventions. Present the proposal; the user confirms, trims, adds. For each domain also collect 2-4 search keywords. Credibility scoring depends on this list being honest, so tell the user: list what you actually know, not what you want to know.
4. **Surfaces.** List the MCPs connected in the session that can read a surface (chat, code review, docs, tickets) and ask which should feed the scan, the same detect-and-opt-in move `/flagrare:standup-report` uses for `extra_mcps`. For each chosen surface, collect its scope by proposing from real data:
   - **chat**: channels, proposed via channel search using team names and domain keywords; include team channels, eng-wide channels, and incident/announcement channels
   - **code review**: repos, proposed from the user's recent activity within the repo scope
   - **docs**: spaces, databases, or folders where RFCs and design docs live, proposed via the doc MCP's search using the domain keywords
   - **tickets**: projects or teams whose comment threads matter, proposed the same way
5. **Audience (optional).** Names whose visibility matters for the promotion case: manager, senior/staff engineers, adjacent team leads. Powers the Audience score; without it that axis defaults to 1 and the skill says so.
6. **Voice.** Fetch a sample of the user's own recent writing (their Slack messages, their PR review comments, not other people's), distill 5-8 observed rules (sentence length, hedging style, formality, emoji use, how they disagree), and write them to `voice.md`. Show the rules for confirmation. If no sample is reachable, fall back to the generic drafting rules below and note it.
7. **Board.** Ask where the board should live (default `~/career-board`) and save it as `skills.career.board.dir`. If the user already keeps a dashboard of these items, point `skills.career.board.dir` at its folder instead of creating a second one. The board itself is created at the end of the first scan (workflow step 7).

Save, then show the full config summary for one final confirmation and set `onboarding_complete: true`.

```json
{
  "github_login": "aturing",
  "display_name": "Alan",
  "repo_scope": "org:acme-corp",
  "skills": {
    "impact-scan": {
      "onboarding_complete": true,
      "slack_handle": "@alan",
      "current_level": "mid",
      "target_level": "senior",
      "target_behaviors": ["influence beyond assigned tickets", "unblocking others", "owning decisions in the billing domain"],
      "domains": [
        { "name": "billing reconciliation", "keywords": ["reconcile", "ledger", "invoice drift"] }
      ],
      "surfaces": [
        { "type": "chat", "mcp": "slack", "scope": ["#eng-billing", "#eng-announcements", "#incidents"] },
        { "type": "code-review", "mcp": "github", "scope": ["acme-corp/billing-service", "acme-corp/payments-api"] },
        { "type": "docs", "mcp": "confluence", "scope": ["ENG space, RFC section"] }
      ],
      "audience": ["grace (manager)", "dknuth (staff)"],
      "exclusions": ["#random", "PRs the user authored"]
    },
    "career": {
      "board": { "dir": "~/career-board" }
    }
  }
}
```

Re-run any onboarding step when the user says "reconfigure", or when they say the scan keeps looking in the wrong places.

## Workflow

### 1. Load state and window

Run the load-state step from Setup first (`career_state.py plan`, applied with the Write tool), then read `career/scan-state.json` (`{ "last_run": iso8601, "seen": [{ "id", "source", "surfaced_at", "status" }] }`). The scan window is `last_run` to now; if no state exists, default to the last 48 hours, capped at 7 days. Items already in `seen` are only re-surfaced if they escalated: a new decision point, a new unanswered question, a thread reopened.

### 2. Sweep in parallel

Spawn **one read-only sweep subagent per configured surface**, all in the same message so they run concurrently. Each gets its surface's scope, the domain map with keywords, the exclusions, the user's identity (so their own posts are skipped), and the time window.

Every sweep hunts the same four signals: (a) a decision still being formed (architecture, API contracts, migrations, process); (b) a question nobody has answered well, or a thread going in circles; (c) a discussion inside the user's domains that is missing context the user has; (d) work from other teams that touches systems the user owns or depends on. And every sweep returns the same shape, raw findings only, no ranking: location and link, participants, a 2-3 sentence summary, matched signal(s), and the specific gap the user could fill.

**Chat sweep (reference: Slack).** Read recent activity in each configured channel, follow interesting threads, and additionally run 2-3 keyword searches from the domain map, since relevant discussions happen outside configured channels. Ignore social chatter, resolved threads, FYI-only announcements, and threads where the right people are already converging.

**Code-review sweep (reference: GitHub).** List open PRs in the configured repos updated within the window and not authored by the user, then read the promising ones including review threads. Also hunt for: PRs whose changed paths touch the user's domains, and approaches carrying a risk the discussion hasn't caught, judged against the domain map's known failure modes. Ignore approved-and-converging PRs, trivial changes, and PRs where requested changes are simply in progress.

**Generic sweep (any other surface: docs, tickets, other chat platforms).** Enumerate items in scope updated within the window (pages, tickets, threads), read the ones with active human discussion, and apply the four signals. On docs surfaces, treat unresolved comment threads and open review periods on RFCs and design docs as prime candidates: they are decisions with explicit windows. Ignore items with no discussion, resolved threads, and pure status updates.

### 3. Score and cut

First get the scoring inputs: run `python3 <plugin root>/lib/career/scoring.py context --home "$HOME"`. It prints `has_map`, the map's `open_rows` (rubric rows not yet done, each with `id`, `area` and `target_text`), `unseen_people` (people who have not seen the user's work yet), and a `fallback` with the configured `target_behaviors` and `audience`.

Score each candidate 0-2 on five axes:

- **Leverage**: would weighing in change the outcome, or just add a voice? A decided thread scores 0.
- **Credibility**: does the user have specific knowledge, context, or ownership the participants lack? Generic "good point" opinions score 0.
- **Stretch**: does this move one of the `open_rows` forward, beyond the user's assigned lane? Pick the row it moves from `open_rows` only, and never invent a row id. With no map or no open rows, use the configured target behaviors instead. Routine work in their own tickets scores low.
- **Audience**: who will see the contribution? 2 if someone in `unseen_people` will, 1 if only people who already know the user's work will, 0 if nobody whose view matters will. With no map, score it against the configured audience the same way; with neither, it defaults to 1.
- **Timing**: is the window still open? A decision landing today scores 2; something simmering for weeks scores 1.

**Hard filter first:** drop anything with Leverage 0 or Credibility 0, regardless of the other axes. That is the anti-performative rule, and it is not negotiable, it protects the user's reputation. Then rank survivors by total and keep at most 5. Dedupe against `scan-state.json` before presenting.

### 4. Present the digest

The digest is a to-do list, not a report. The user should know what to do from the table alone, and read an item's block only when they act on it. Write the table for a reader who has read none of these threads and remembers nothing from the scan: they may open it hours later, or see it re-listed mid-session after other work. A row that only makes sense to someone who just ran the sweeps has failed, however short it is.

Do not relay each sweep's findings as it lands; the digest is the only output. When a status line is forced (a sweep finishing, the harness asking for an update), give one line naming the sweeps still running, with no findings.

```
## Impact scan: <date>, <window>. <one line of caveats: surfaces skipped, state not saved>

| # | What's going on | What you'd do | Why it matters | Next step |
|---|---|---|---|---|
| 1 | <whose thing, what it is in product terms, where it stands; the thing's name is the link> | <verb-first move, plain words> | <impact, max 12 words> · <target behavior> | Send draft |
| 2 | A restaurant got no email or text for two app orders on 9/24; a support lead asked in the [squad channel](<permalink>) whether it should have, nobody answered | Tell them which email should have fired and whether it did | A partner missed real orders, support is stuck · unblocking others | Check first: look the order up in the email tool |

### 1. <same verb-first action>
<one sentence: what is happening and where it stands>. <one sentence: why you, naming the fact or context only you bring>.
> <draft, at most 3 sentences>

(repeat per item)

**Cut:** <near-miss, reason>; <near-miss, reason>; ...
**Flags raised:** <map section>: <what changed> (only when step 6 raised a flag)
**Handed off:** <problem in plain words> (seen <N> times, now a candidate in `initiatives.json`) (only when step 6 handed one off)
```

Rules that keep it scannable:

- **"What's going on" gives the context before the ask.** One plain sentence, 25 words at most: whose thing it is, what it is in product terms, and where it stands (unreviewed, approved, question unanswered since Tuesday). "a teammate's [peak-times PR](url) promises a fallback message when loading fails; two people approved it", not "the peak-times fallback PR". The thing's name carries the link, so there is no separate Where column.
- **The table speaks product, not code.** No PR numbers, ticket keys, channel ids, function names, or flags in any table cell: a reader cannot decode "a missing error flag on a PR number" without the context they don't have. Say what breaks for whom ("a server error shows the full-page error screen instead of the retry button"). Code identifiers and `file:line` belong in the item block and the draft, where the reader is already acting.
- **Actions start with a verb and name the move in plain words**: "Point out that a server error blanks the page instead of showing the retry", not "Flag a missing error flag on a PR number", and not "Item report error handling".
- **Re-listing follows the same rules.** When remaining items are shown again later in the session, rebuild each row from scratch for a cold reader; never shorten a row to "the same gap" or "item 1's issue" because it was discussed earlier.
- **"Why it matters" says what changes if the user acts, then the behavior it exercises.** The impact is 12 words at most, the concrete outcome ("stops a 502 blanking a page before launch", "a modifiers decision is being made without the person who designed them"), never the score or a restatement of the action. After a `·`, name what it exercises in two or three plain words: the rubric row's area when there is a map ("finding problems"), otherwise the configured target behavior ("quality bar", "unblocking others"). Row ids are code-like, so they go in the item block, never in the table. Rows are ordered by score, so this column is what explains the ranking.
- **Every item ends in a next step.** Either a draft ready to send, or `Check first:` with the single concrete check (a query, a code path to trace) that would make a draft safe. Never a draft built on a claim that has not been verified.
- **No field labels in item blocks** ("What's happening:", "Why you:", "Suggested angle:"). The two sentences and the draft carry all of it.
- **Evidence goes inside the draft, not before it.** If the draft already cites `file:line`, the block does not repeat it.
- **Near misses fit on one line.** A short reason each, so the filter stays honest and tunable without adding a section.
- **Stop after the cut line** (and the flags and hand-off lines when present). No closing summary. Ask only which items to act on.

### 5. Drafting rules

Read `voice.md` first if it exists; its observed rules win over the generic ones. Generic floor, applied always:

1. **Short and direct.** Three sentences at most, no preamble, no "Great discussion!", no wrap-up flourish.
2. **No LLM tells.** No em-dashes, no "aligns with", no rule-of-three constructions, no self-congratulation.
3. **First person, explicit.** "I ran into this", never "Ran into this".
4. **Hedge pushback collaboratively, without interrogating.** State the concern plainly with its evidence and admit possible missing context. A closing question is for genuine uncertainty, when you actually need the author's context to resolve the point, not a mandatory sign-off: ending every draft with "does that match your understanding?" reads as a tic, and a faux-question that is really an assertion ("am I reading this right that this is unused?") reads passive-aggressive, which is worse than asserting. When the evidence is on the table and you are confident, say the thing and stop.
5. **Contextualize references.** Never a bare ticket number; say what the ticket is with the key in parentheses.
6. **Cite PRs and commits, not people.** Explaining where a behavior came from means pointing at the PR or SHA, never naming who broke it.
7. **Substance first.** Every draft must contain the specific fact, risk, or suggestion that justified surfacing the item. If someone without the user's context could have written the draft, the item fails the credibility bar: cut it instead of shipping filler.

**Never post anything anywhere.** Every draft waits for the user's explicit approval of that specific message. Posting without it is the one unforgivable failure of this skill.

### 6. Update state and the evidence trail

After presenting, write `career/scan-state.json` with the Write tool: update `last_run`, append surfaced items with `status: "surfaced"`. If the write fails, say so in the digest's caveat line, since the next run will re-surface the same items. Then update the board (step 7) in the same turn.

When the user approves and posts a contribution (or says they handled it), set that item's status to `"contributed"` and append to `career/contributions.log.md`:

```
- <date> | <link> | <one sentence: what the contribution was and what it changed> | behavior: <target behavior exercised> | row: <rubric row id>
```

Add the `| row: <id>` field only when there is a map and the item moved one of its `open_rows`; otherwise end the line after `behavior:`. The format is in `<plugin root>/lib/career/STATE.md`.

This log is the promotion evidence trail, the lagging indicator made legible. When the user later runs `/flagrare:brag-doc` or builds a promo packet, point them at it; brag-doc should treat it as a first-class source.

Every log entry is also a board update: rebuild so the evidence log shows it, and move the item to `waiting` (a reply is expected) or `done`.

### 6b. Flags and hand-off

Two small records keep the other career skills current. Write both with the Write tool from the action the script prints, reading the target first if it exists.

**Staleness flags.** When a sweep sees something that makes part of the promotion map out of date, raise a flag for that map section: a reorg or team change (`org`), someone leaving or a new manager or director (`org` and `people`), a change to the promotion process (`process`), HR publishing the review calendar (`calendar`). Run `python3 <plugin root>/lib/career/career_state.py flag --home "$HOME" --section <section> --reason "<what changed, plain words>" --source <link> --today <YYYY-MM-DD>`. The same flag is never raised twice. Only raise flags when the user has a promotion map.

**Hand-off of recurring problems.** Some items are problems rather than decisions: something broken, missing, or painful for users or partners (a class of failures, a gap nobody owns, the same question asked again). Record each problem-type item that passes the hard filter, whether or not it makes the top 5, once per scan run: `python3 <plugin root>/lib/career/career_state.py candidate --home "$HOME" --id <stable-slug> --title "<problem in plain words>" --evidence <link> --today <YYYY-MM-DD>`. To find an earlier sighting, compare with the existing candidates in `initiatives.json` by title and evidence; reuse that id when it is the same underlying problem, otherwise choose a new stable slug. A second sighting means the same problem showing up somewhere else (a different thread, incident or ticket), not the same thread continuing; the script ignores an evidence link it already has, so an escalating thread never counts twice.

When the planned `initiatives.json` content shows that candidate's `seen_count` at 2 or more, the problem is handed off: it leaves the table (it does not take one of the 5 slots), appears only on the digest's **Handed off** line, and goes into `scan-state.json` with status `handed_off`. Owning the fix is worth more than a third comment. The candidates wait in `initiatives.json` for `/flagrare:opportunity-scan` (coming in a later release).

### 7. Keep the board current

The board is the expected output of every scan, not an extra: a local page the user opens to see what to act on next, what is waiting on someone else, and the evidence log. The digest is read once; the board is what they come back to. It is display-only: `data.json` is the single source of truth, the user tells you in chat what changed, and you update the file and rebuild.

**First scan, or no board yet.** If no board directory is configured under either `skills.career.board.dir` or `skills["senior-scan"].board.dir` (including users onboarded before the board existed) or the folder has no `data.json`, create it at the end of this run: ask for the location once (default `~/career-board`), save it as `skills.career.board.dir`, write `data.json` from this scan, build, and tell the user how to open it. Never finish a scan with no board and no caveat saying why.

**Every update.** Write `<board dir>/data.json` with the Write tool, then run `python3 <plugin root>/lib/career/board/build.py <board dir>`, which renders `board.html` from the bundled template plus the contributions log (it reads the career log and any entries still only in the old senior-scan log). If the sandbox blocks the write outside the working folder, rerun the build outside the sandbox. Rebuild after the scan AND whenever an item changes (a draft posted, an item now waiting on someone, done, dropped), in the same turn you update `scan-state.json` or the log, so the board never lags the conversation. If the build fails, say so in the caveat line.

`data.json` shape:

```json
{
  "scan": { "date": "2026-09-30", "window": "Sep 29 14:18 UTC to Sep 30 13:30 UTC", "caveats": "Jira skipped" },
  "behaviors": ["raising the quality bar", "unblocking others"],
  "items": [{
    "id": "short-stable-slug", "rank": 1, "status": "todo",
    "urgency": "today", "effort": "15 min", "deadline": "2 approvals, could merge today",
    "source": "github", "kind": "review",
    "action": "Point out the flyout always shows the last 7 days",
    "link": "https://...", "context": "Whose thing, what it is, where it stands",
    "why": "Impact in 12 words or less", "behavior": "raising the quality bar", "rubric_rows": ["scope.proactive-discovery"],
    "draft": "ready-to-send text", "draft_where": "GitHub inline comment on file.js:60",
    "check_first": "the one check that makes a draft safe",
    "waiting_on": "a reviewer", "since": "2026-09-29"
  }]
}
```

- `status`: `todo` (shown in the ranked list), `waiting` (raised, waiting on someone; set `waiting_on` and `since`, and after 3 days the board suggests a nudge), `done`, `dropped`.
- `urgency`: `today` (could merge or close before the user acts), `week`, `later`. `deadline` says why.
- `behaviors`: the configured target behaviors; the board shows evidence coverage for each.
- `rubric_rows`: optional; the ids of the map rows the item moves (from `open_rows`), empty or absent without a map.
- An item carries either `draft` or `check_first`, never a draft built on an unverified claim. The same product-language rules as the digest table apply to `action`, `context` and `why`.
- Keep ids stable across runs. Before adding an item, check for an existing one about the same thread: update it instead of adding a duplicate, and if the new scan contradicts its text, fix the text or flag the conflict to the user.
````

- [ ] **Step 2: Write `evals/fixtures/promotion-map.json`**

```json
{
  "target": {
    "current_level": {"value": "Software Engineer III", "source": "https://example.com/ladder", "checked_at": "2026-09-30", "status": "verified"},
    "target_level": {"value": "Senior Software Engineer", "source": "https://example.com/ladder", "checked_at": "2026-09-30", "status": "verified"}
  },
  "rubric": {
    "rows": [
      {"id": "scope.proactive-discovery", "area": "Scope & Impact", "status": "partial",
       "current_text": {"value": "Given a problem, finds the right solution", "source": "https://example.com/ladder", "checked_at": "2026-09-30", "status": "verified"},
       "target_text": {"value": "Proactively discovers and solves problems the team is facing", "source": "https://example.com/ladder", "checked_at": "2026-09-30", "status": "verified"},
       "evidence": []},
      {"id": "craft.review-quality", "area": "Technical Craft", "status": "done",
       "current_text": {"value": "Timely, constructive reviewer", "source": "https://example.com/ladder", "checked_at": "2026-09-30", "status": "verified"},
       "target_text": {"value": "Sought-after reviewer for their stack", "source": "https://example.com/ladder", "checked_at": "2026-09-30", "status": "verified"},
       "evidence": ["- 2026-09-20 | https://example.com/pr/1 | caught a data-loss bug in review | behavior: raising the quality bar"]}
    ]
  },
  "people": [
    {"name": "Sam Rivera", "role": {"value": "Engineering Manager", "source": "https://example.com/org", "checked_at": "2026-09-30", "status": "verified"}, "relation": "current manager", "seen_your_work": true, "evidence": [], "confirmed_by_user": true},
    {"name": "Alex Chen", "role": {"value": "Director of Engineering", "source": "https://example.com/org", "checked_at": "2026-09-30", "status": "verified"}, "relation": "skip level, starts next month", "seen_your_work": false, "evidence": [], "confirmed_by_user": true}
  ],
  "sections": {"target": {"checked_at": "2026-09-30", "sources": []}, "rubric": {"checked_at": "2026-09-30", "sources": []}, "people": {"checked_at": "2026-09-30", "sources": []}}
}
```

- [ ] **Step 3: Write `evals/evals.json`**

```json
{
  "skill_name": "impact-scan",
  "evals": [
    {
      "id": 0,
      "prompt": "Run an impact scan. Two threads look equally strong on leverage, credibility and timing: one is a question about why our checkout fails for some partners that nobody has investigated, the other is a style debate about code formatting in a module I own. My promotion map is at ~/.claude/skills/flagrare/career/promotion-map.json (see the fixture).",
      "expected_output": "Agent runs scoring.py context, sees the open rubric row scope.proactive-discovery (Scope & Impact) and that Alex Chen has not seen the user's work, ranks the unexplained checkout failure above the formatting debate because it moves the open row, names 'finding problems' (not the row id) in the Why it matters cell, and puts the row id only in the item block.",
      "files": ["evals/fixtures/promotion-map.json"]
    },
    {
      "id": 1,
      "prompt": "Run an impact scan. In the eng-wide channel this week there is an announcement that our director is leaving and a new director starts next month. I have a promotion map.",
      "expected_output": "Agent raises a staleness flag for the org section (and people) with career_state.py flag, the announcement link as source, writes flags.json with the Write tool, and shows a 'Flags raised' line after the Cut line. It does not add the announcement as a weigh-in item unless there is a real decision to shape.",
      "files": ["evals/fixtures/promotion-map.json"]
    },
    {
      "id": 2,
      "prompt": "Run an impact scan. A partner support thread today reports order emails not arriving; last week a different incident thread reported the same missing emails and it was recorded as a candidate in initiatives.json with seen_count 1.",
      "expected_output": "Agent records the new sighting with career_state.py candidate reusing the existing id and the new thread's link, sees seen_count reach 2, does not draft a reply for it, keeps it out of the top-5 table, lists it on the 'Handed off' line, and marks it handed_off in scan-state.json.",
      "files": []
    }
  ]
}
```

- [ ] **Step 4: Verify and commit**

```bash
python3 -c "t=open('plugins/flagrare/skills/impact-scan/SKILL.md').read();assert t.startswith('---\nname: impact-scan\n');print('ok')"
python3 -c "import json;json.load(open('plugins/flagrare/skills/impact-scan/evals/evals.json'));print('evals ok')"
python3 plugins/flagrare/lib/career/map_schema.py check plugins/flagrare/skills/impact-scan/evals/fixtures/promotion-map.json --today 2026-09-30
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/skills/impact-scan/SKILL.md plugins/flagrare/skills/impact-scan/evals/evals.json plugins/flagrare/skills/impact-scan/evals/fixtures/promotion-map.json
git add plugins/flagrare/skills/impact-scan
git commit -m "✨ feat(impact-scan): score against the promotion map, raise flags, hand off recurring problems"
```
Expected: `ok`, `evals ok`, a check result with `"errors": []`, and `0`.

---

### Task 5: README, CHANGELOG and local release 1.45.0

**Files:** `README.md`, `CHANGELOG.md`, `plugins/flagrare/.claude-plugin/plugin.json`

- [ ] **Step 1: README**

At the end of the paragraph that starts "`/flagrare:impact-scan` (formerly `/flagrare:senior-scan`", append this sentence:

"With a promotion map from `/flagrare:promotion`, it scores items against your open rubric rows and the people who haven't seen your work yet, raises flags when part of the map goes stale, and hands problems that keep coming back to `initiatives.json` instead of drafting another reply."

- [ ] **Step 2: Tests and README commit**

```bash
python3 -m unittest discover -s plugins/flagrare/lib/career/tests
git diff README.md | python3 -c "import sys;print(sum(l.count(chr(0x2014)) for l in sys.stdin if l.startswith('+')))"
git add README.md
git commit -m "📝 docs(readme): impact-scan uses the promotion map"
```

- [ ] **Step 3: Version and CHANGELOG**

```bash
python3 scripts/bump-version.py 1.45.0
python3 -c "import json;print(json.load(open('plugins/flagrare/.claude-plugin/plugin.json'))['version'])"
```
Expected: `1.45.0`.

Insert at the top of `CHANGELOG.md`, under `# Changelog` and its blank line, above `## 1.44.0`:

```markdown
## 1.45.0: 2026-09-30

The scan finally knows where you're going.

### Improved Skills

- **`/flagrare:impact-scan`, scored against your promotion map**: the Stretch axis used to mean "exercises one of the behaviors you typed at onboarding", a list that never changes as you close gaps. Field-tested the hard way: a day of promotion research produced the rubric rows still open and the directors who had never seen the user's work, and the scan could use none of it. With a map, Stretch now asks which open rubric row an item moves (chosen from the map's rows, never invented), and Audience asks whether someone who hasn't seen your work will see it. The digest names the area in plain words and keeps the row id out of the table, and posted contributions carry an optional `| row: <id>` tag. When a sweep sees a reorg, a departure or a published review calendar, the scan raises a flag so the next `/flagrare:promotion` refresh re-checks that part of the map. Problems that keep coming back from different threads are recorded in `initiatives.json`; on the second sighting the scan hands the problem off instead of drafting another comment, ready for the upcoming `/flagrare:opportunity-scan`. Without a map, nothing changes.

### Tooling

- **Career library**: `scoring.py context` lists what the scan scores against (open rows, people who haven't seen your work, or the config fallback), and `career_state.py flag` and `candidate` plan the flag and candidate files without writing them. A thread that keeps escalating never counts as a second sighting, and a reworded flag with the same source is not raised twice. The first evals for impact-scan cover map-aware ranking, flags and hand-off.

```

- [ ] **Step 4: Local release commit and tag (do not push)**

```bash
git diff CHANGELOG.md | python3 -c "import sys;print(sum(l.count(chr(0x2014)) for l in sys.stdin if l.startswith('+')))"
git add CHANGELOG.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "🔖 release: v1.45.0"
git tag -a v1.45.0 -m "release v1.45.0" HEAD
```
The controller asks the user before pushing, the GitHub release and `/flagrare:update`.

---

## As built

The shipped 1.45.0 differs from the tasks above in these ways, each decided during review:

- **Flags and hand-off moved from step 6b to step 3b and run only with a map.** The plan put them after the digest, so a handed-off problem could still take a top-5 slot and the digest could not show the Flags raised or Handed off lines. They now run after the hard filter and before the cut. Without a map the step is skipped, which keeps the promise that nothing changes without one.
- **The scan reads `scoring.py context` in step 1, and with a map the sweeps return a separate list of map events** (reorg, departure, new manager or director, promotion process change, review calendar). The plan had flags raised from ranked items, but sweeps ignore announcements and an announcement has no leverage, so flags could never fire.
- **Audience falls back to the configured audience when `unseen_people` is empty** (no map, a map with no people yet, or everyone has seen the work), with the pre-1.45 wording.
- **Hand-off details:**
  - Every sighting in a run is recorded before hand-offs are decided.
  - `seen_count` is read from `initiatives.json` when the script plans nothing.
  - The Handed off line says "recorded in `initiatives.json`".
- **"Why it matters" names what the open row asks for, taken from its `target_text`,** not the row's area. The row id sits in parentheses at the end of the item block's "why you" sentence. With a map, `behavior:` still names the closest configured behavior (the board counts those), and the row id goes in `row:`.
- **Evals:** eval 0 expects the plain-words phrase. Eval 2 gains `evals/fixtures/initiatives.json` and a map.
- **`STATE.md`:** the hand-off threshold is stated as impact-scan's rule, not the script's, and applies only when the user has a promotion map.

Parked for later:
- Corrupt `flags.json` or `initiatives.json` is replaced wholesale, and item-level corruption can raise.
- A config that is not a dict raises in `scoring.context`.
- There are no CLI tests.
- Whether a problem already marked `handed_off` is re-listed on later runs.
- Wording nits:
  - The row id placeholder says "only with a map" rather than "only when it moves an open row".
  - The sweep inputs list does not name `has_map`.
- Spec Milestone 2 item 5 is left open for a product decision: every chat draft ends with its link, and every claim is hedged. It conflicts with the drafting rule "say the thing and stop".
