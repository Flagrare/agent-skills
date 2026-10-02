# Measure impact, Milestone 2: reminders. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan's output. Check a file with `grep -n $'—' <files>` (no output means clean).

**Goal:** Remind the user to measure impact at the right moments, without nagging: one line at session start when something is due, and a short note to Claude when a measurable moment happens in a session.

**Architecture:** One Python hook module, `plugins/flagrare/hooks/measure_reminders.py`, with two entry points (`session-start`, `moment`) and pure functions the tests call directly. It reuses `lib/career/measurements.py` (Milestone 1) for "what is due" and the saved skips, reads the shared config for `skills["measure-impact"].reminders`, and keeps a per-session list of moments already mentioned in the temp folder. It never fails a session: any error means no output and exit 0. `hooks.json` registers it for `SessionStart` (matcher `startup`) and `PostToolUse` (matcher `Skill|Bash|Write|Edit`).

**Tech Stack:** Python 3 standard library, `unittest`, Claude Code plugin hooks (`hooks/hooks.json`, `${CLAUDE_PLUGIN_ROOT}`).

**Spec:** `docs/plans/2026-10-02-measure-impact-design.md`, section "Reminders" (approved 2026-10-02). Milestone 1 (v1.57.0) built `measurements.py`; read its `due`, `load`, `CorruptFile` before starting.

## Global Constraints

- No em-dashes in any file this plan creates or edits.
- Fixtures are invented (Acme Pizza, Kai, Sam); no real company data.
- Test names: `test_given_<state>_when_<action>_then_<outcome>`.
- Hook output follows the Claude Code hook contract: a JSON object on stdout; `systemMessage` is shown to the user; `hookSpecificOutput.additionalContext` (with `hookEventName`) reaches Claude. For `PostToolUse`, plain stdout and stderr with exit 0 reach nobody, so only `additionalContext` is used.
- A hook must never block or break the session: every path exits 0, and an internal error produces no output.
- Noise rules from the spec: an item is mentioned at most once per session; skipped items stay silent; `skills["measure-impact"].reminders: false` silences everything; small fixes and scheduled runs are left to Claude's judgment through the note's wording.
- Commits are gitmoji conventional commits straight to `main`, no AI attribution lines.
- Tests run from `plugins/flagrare/lib/career`: `python3 -m unittest discover -s tests -q`.

## Review Focus

1. **Garbage on stdin** (empty, not JSON, a JSON list): the moment hook prints nothing and exits 0. Test in Task 2.
2. **A corrupt `measurements.json` at session start:** one readable line naming the file, never a traceback. Test in Task 1.
3. **The same moment twice in one session:** the second is silent; a different ticket still gets its note. Test in Task 2.
4. **No `session_id`, or a temp folder that can't be written:** the note still goes out (no dedupe), no crash. Test in Task 2.
5. **`reminders: false`:** both hooks are silent, even when things are due. Tests in Tasks 1 and 2.

---

## File structure

- Create `plugins/flagrare/hooks/measure_reminders.py`: the hook module.
- Create `plugins/flagrare/lib/career/tests/test_measure_reminders.py`: its tests (the suite already runs from here).
- Modify `plugins/flagrare/hooks/hooks.json`: register both hooks.
- Modify `plugins/flagrare/skills/measure-impact/SKILL.md`: a "Reminders" section (what fires, how to turn it off, the one memory line to suggest for plain conversation).
- Modify `README.md`: one sentence about reminders in the measure-impact paragraph.
- Modify `CHANGELOG.md`, `plugins/flagrare/.claude-plugin/plugin.json` (release).

---

### Task 1: The session-start reminder

**Files:**
- Create: `plugins/flagrare/hooks/measure_reminders.py`
- Test: `plugins/flagrare/lib/career/tests/test_measure_reminders.py`

**Interfaces:**
- Consumes: `measurements.due(home, today) -> dict` (keys `checks_due`, `bets_waiting`, `unmeasured_wins`, `count`), `measurements.CorruptFile`, `career_state.paths(home)["config"]`.
- Produces: `reminders_on(home: str) -> bool`; `session_start(home: str, today: str) -> dict | None` (a hook JSON object, or `None` for no output).

- [ ] **Step 1: Write the failing tests**

Create `plugins/flagrare/lib/career/tests/test_measure_reminders.py`:

```python
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import measure_reminders as mr  # noqa: E402

CAREER = ".claude/skills/flagrare/career"
CONFIG = ".claude/skills/flagrare/config.json"


def write(home: Path, rel: str, text: str) -> None:
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def measurement(**over) -> dict:
    base = {"id": "acme-reorder", "work": {"title": "Reorder button for Acme Pizza", "link": "https://tracker.example/T-1", "kind": "ticket"},
            "stage": "before", "launch_date": "2026-10-01",
            "checks": [{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14}],
            "created_at": "2026-09-20", "updated_at": "2026-10-01"}
    base.update(over)
    return base


class SessionStart(unittest.TestCase):
    def test_given_nothing_saved_when_a_session_starts_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(mr.session_start(d, "2026-10-16"))

    def test_given_a_check_due_when_a_session_starts_then_shows_one_line_and_tells_claude_the_details(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([measurement()]))
            out = mr.session_start(d, "2026-10-16")
            self.assertEqual(out["systemMessage"], "Impact: 1 check due (Reorder button for Acme Pizza). Ask Claude to measure it when you have a minute.")
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
            self.assertIn("acme-reorder", out["hookSpecificOutput"]["additionalContext"])

    def test_given_checks_and_recent_wins_due_when_a_session_starts_then_counts_each_kind(self):
        with tempfile.TemporaryDirectory() as d:
            two = measurement(checks=[{"due": "2026-10-15", "done_at": None, "value": None, "verdict": None, "after_days": 14},
                                      {"due": "2026-10-16", "done_at": None, "value": None, "verdict": None, "after_days": 42}])
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([two]))
            write(Path(d), f"{CAREER}/contributions.log.md", "- 2026-10-10 | https://chat.example/p1 | Helped Sam | behavior: x\n")
            out = mr.session_start(d, "2026-10-16")
            self.assertEqual(out["systemMessage"], "Impact: 2 checks due (Reorder button for Acme Pizza, and more), 1 recent win with no number. Ask Claude to measure them when you have a minute.")

    def test_given_reminders_turned_off_when_a_session_starts_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([measurement()]))
            write(Path(d), CONFIG, json.dumps({"skills": {"measure-impact": {"reminders": False}}}))
            self.assertIsNone(mr.session_start(d, "2026-10-16"))

    def test_given_a_corrupt_file_when_a_session_starts_then_names_the_file_in_one_line(self):
        with tempfile.TemporaryDirectory() as d:
            write(Path(d), f"{CAREER}/measurements.json", "[{oops")
            out = mr.session_start(d, "2026-10-16")
            self.assertIn("measurements.json", out["systemMessage"])
            self.assertNotIn("Traceback", out["systemMessage"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_reminders -q`
Expected: error, `ModuleNotFoundError: No module named 'measure_reminders'`.

- [ ] **Step 3: Implement**

Create `plugins/flagrare/hooks/measure_reminders.py`:

```python
#!/usr/bin/env python3
"""Reminder hooks for /flagrare:measure-impact.

`session-start` (SessionStart): one line for the user when measurements are due.
`moment` (PostToolUse): a short note for Claude when a measurable moment happens.
Neither may ever break a session: any error means no output and exit 0.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib" / "career"))

import career_state  # noqa: E402
import measurements  # noqa: E402


def reminders_on(home: str) -> bool:
    try:
        config = json.loads(Path(career_state.paths(home)["config"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    block = ((config.get("skills") or {}).get("measure-impact") or {}) if isinstance(config, dict) else {}
    return block.get("reminders", True) is not False


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def session_start(home: str, today: str) -> dict | None:
    if not reminders_on(home):
        return None
    try:
        due = measurements.due(home, today)
    except measurements.CorruptFile as exc:
        return {"systemMessage": f"Impact: {exc}"}
    if not due["count"]:
        return None
    parts = []
    checks = due["checks_due"]
    if checks:
        more = ", and more" if len(checks) > 1 else ""
        parts.append(f"{_plural(len(checks), 'check')} due ({checks[0]['title']}{more})")
    if due["bets_waiting"]:
        parts.append(f"{_plural(len(due['bets_waiting']), 'bet')} waiting for a launch date")
    if due["unmeasured_wins"]:
        parts.append(f"{_plural(len(due['unmeasured_wins']), 'recent win')} with no number")
    pronoun = "it" if due["count"] == 1 else "them"
    line = f"Impact: {', '.join(parts)}. Ask Claude to measure {pronoun} when you have a minute."
    context = ("measure-impact items due (from measurements.py due): " + json.dumps(due, ensure_ascii=False)
               + ". Mention them once, at a natural point; never interrupt the user's current task for them.")
    return {"systemMessage": line, "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}
```

- [ ] **Step 4: Run them to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_reminders -q`
Expected: `OK` (5 tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/hooks/measure_reminders.py plugins/flagrare/lib/career/tests/test_measure_reminders.py
git commit -m "✨ feat(measure-impact): a one-line reminder at session start when measurements are due"
```

---

### Task 2: The in-session moment note and the command line

**Files:**
- Modify: `plugins/flagrare/hooks/measure_reminders.py`
- Test: `plugins/flagrare/lib/career/tests/test_measure_reminders.py`

**Interfaces:**
- Consumes: `reminders_on`, `measurements.load(home)`, `measurements.CorruptFile`.
- Produces:
  - `MOMENT_SKILLS: dict[str, tuple[str, str]]` (skill name to what happened and the stage);
  - `moment_of(event: dict) -> tuple[str, str, str] | None` (`(dedupe_key, what, stage)`);
  - `moment(event: dict, home: str, state_dir: str) -> dict | None`;
  - `main(argv: list[str], stdin_text: str, home: str, today: str, state_dir: str) -> str` (the JSON text to print, or `""`), and the `__main__` block that always exits 0.

- [ ] **Step 1: Write the failing tests**

Append to `test_measure_reminders.py`, before the `if __name__` line:

```python
def skill_event(name: str, args: str = "", sid: str = "s1") -> dict:
    return {"session_id": sid, "hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": {"skill": name, "args": args}}


class Moment(unittest.TestCase):
    def test_given_a_tdd_was_drafted_when_the_tool_finishes_then_tells_claude_to_offer_a_before_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            out = mr.moment(skill_event("flagrare:tdd-writer", "T-5"), d, s)
            note = out["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PostToolUse")
            self.assertIn("a TDD was drafted", note)
            self.assertIn("before stage", note)

    def test_given_an_unrelated_skill_when_the_tool_finishes_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            self.assertIsNone(mr.moment(skill_event("flagrare:design-review"), d, s))

    def test_given_a_pr_merge_command_when_it_finishes_then_offers_an_after_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "gh pr merge 42 --squash"}}
            self.assertIn("after stage", mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"])

    def test_given_a_contributions_log_write_when_it_finishes_then_offers_a_past_measurement(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            event = {"session_id": "s1", "tool_name": "Edit", "tool_input": {"file_path": f"{d}/{CAREER}/contributions.log.md"}}
            self.assertIn("past stage", mr.moment(event, d, s)["hookSpecificOutput"]["additionalContext"])

    def test_given_the_same_moment_twice_in_a_session_when_it_finishes_then_the_second_is_silent(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            self.assertIsNotNone(mr.moment(skill_event("flagrare:work-prep", "T-5"), d, s))
            self.assertIsNone(mr.moment(skill_event("flagrare:work-prep", "T-5"), d, s))
            self.assertIsNotNone(mr.moment(skill_event("flagrare:work-prep", "T-6"), d, s))

    def test_given_reminders_turned_off_when_a_moment_happens_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            write(Path(d), CONFIG, json.dumps({"skills": {"measure-impact": {"reminders": False}}}))
            self.assertIsNone(mr.moment(skill_event("flagrare:tdd-writer"), d, s))

    def test_given_skipped_work_when_its_moment_happens_then_says_nothing(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            skipped = {"id": "typo-fix", "work": {"title": "Fix a typo", "link": "https://tracker.example/T-9", "kind": "ticket"},
                       "stage": "skipped", "skipped_reason": "small fix"}
            write(Path(d), f"{CAREER}/measurements.json", json.dumps([skipped]))
            self.assertIsNone(mr.moment(skill_event("flagrare:work-prep", "https://tracker.example/T-9"), d, s))

    def test_given_no_session_id_when_a_moment_happens_then_still_notes_it(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            self.assertIsNotNone(mr.moment(skill_event("flagrare:tdd-writer", sid=""), d, s))

    def test_given_an_unwritable_state_folder_when_a_moment_happens_then_still_notes_it(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNotNone(mr.moment(skill_event("flagrare:tdd-writer"), d, "/nonexistent/folder/for/state"))


class CommandLine(unittest.TestCase):
    def test_given_garbage_on_stdin_when_the_moment_hook_runs_then_prints_nothing_and_exits_0(self):
        for text in ["", "not json", "[1, 2]"]:
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
                    self.assertEqual(mr.main(["x", "moment"], text, d, "2026-10-16", s), "")
                script = HOOKS / "measure_reminders.py"
                done = subprocess.run([sys.executable, str(script), "moment"], input=text, capture_output=True, text=True)
                self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_given_a_moment_on_stdin_when_the_hook_runs_then_prints_the_json_note(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as s:
            out = mr.main(["x", "moment"], json.dumps(skill_event("flagrare:open-pr")), d, "2026-10-16", s)
            self.assertIn("a PR was opened", json.loads(out)["hookSpecificOutput"]["additionalContext"])
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_reminders -q`
Expected: errors, `AttributeError: module 'measure_reminders' has no attribute 'moment'`.

- [ ] **Step 3: Implement**

Append to `measure_reminders.py`:

```python
MOMENT_SKILLS = {
    "flagrare:tdd-writer": ("a TDD was drafted", "before"),
    "flagrare:work-prep": ("a ticket was picked up", "before"),
    "flagrare:intake": ("a ticket was picked up", "before"),
    "flagrare:opportunity-scan": ("projects were proposed", "before"),
    "flagrare:open-pr": ("a PR was opened", "before"),
    "flagrare:release-check": ("a release went out", "after"),
}


def moment_of(event: dict) -> tuple[str, str, str] | None:
    tool = event.get("tool_name")
    data = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    if tool == "Skill" and data.get("skill") in MOMENT_SKILLS:
        what, stage = MOMENT_SKILLS[data["skill"]]
        return f"skill:{data['skill']}:{str(data.get('args', ''))[:120]}", what, stage
    if tool == "Bash":
        command = str(data.get("command", ""))
        if "gh pr merge" in command:
            return f"merge:{command[:120]}", "a PR was merged", "after"
        if "gh pr create" in command:
            return f"create:{command[:120]}", "a PR was opened", "before"
    if tool in ("Write", "Edit") and str(data.get("file_path", "")).endswith("career/contributions.log.md"):
        return "log", "a contribution was logged", "past"
    return None


def _skipped(event: dict, home: str) -> bool:
    try:
        items = measurements.load(home)
    except measurements.CorruptFile:
        return False
    text = json.dumps(event.get("tool_input") or {}, ensure_ascii=False)
    for item in items:
        if isinstance(item, dict) and item.get("stage") == "skipped":
            link = (item.get("work") or {}).get("link") or ""
            if (link and link in text) or (len(str(item.get("id", ""))) > 3 and str(item["id"]) in text):
                return True
    return False


def _first_time(session_id: str, key: str, state_dir: str) -> bool:
    if not session_id:
        return True
    path = Path(state_dir) / f"flagrare-measure-{session_id}.json"
    try:
        seen = json.loads(path.read_text(encoding="utf-8"))
        seen = seen if isinstance(seen, list) else []
    except (OSError, json.JSONDecodeError):
        seen = []
    if key in seen:
        return False
    try:
        path.write_text(json.dumps(seen + [key]), encoding="utf-8")
    except OSError:
        pass
    return True


def moment(event: dict, home: str, state_dir: str) -> dict | None:
    if not isinstance(event, dict) or not reminders_on(home):
        return None
    found = moment_of(event)
    if not found:
        return None
    key, what, stage = found
    if _skipped(event, home) or not _first_time(str(event.get("session_id") or ""), key, state_dir):
        return None
    note = (f"Measure-impact moment: {what}. Unless this is a small fix, the user already measured or skipped this work, "
            f"or this is a scheduled run, offer /flagrare:measure-impact ({stage} stage) in one short line at the end of your reply. "
            "Do not interrupt the current task for it, and do not offer it again for this work in this session.")
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}


def main(argv: list[str], stdin_text: str, home: str, today: str, state_dir: str) -> str:
    mode = argv[1] if len(argv) > 1 else ""
    try:
        if mode == "session-start":
            out = session_start(home, today)
        elif mode == "moment":
            event = json.loads(stdin_text) if stdin_text.strip() else {}
            out = moment(event, home, state_dir) if isinstance(event, dict) else None
        else:
            out = None
    except Exception:  # a reminder must never break the session
        return ""
    return json.dumps(out, ensure_ascii=False) if out else ""


if __name__ == "__main__":
    try:
        text = sys.stdin.read()
    except Exception:
        text = ""
    printed = main(sys.argv, text, os.path.expanduser("~"), date.today().isoformat(), tempfile.gettempdir())
    if printed:
        print(printed)
    sys.exit(0)
```

- [ ] **Step 4: Run them to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_reminders -q`
Expected: `OK` (16 tests).

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/hooks/measure_reminders.py plugins/flagrare/lib/career/tests/test_measure_reminders.py
git commit -m "✨ feat(measure-impact): a short note to Claude when a measurable moment happens, once per session"
```

---

### Task 3: Register the hooks and document them

**Files:**
- Modify: `plugins/flagrare/hooks/hooks.json`
- Modify: `plugins/flagrare/skills/measure-impact/SKILL.md`
- Modify: `README.md`
- Test: `plugins/flagrare/lib/career/tests/test_measure_reminders.py`

**Interfaces:**
- Consumes: the module's `session-start` and `moment` entry points.
- Produces: the registered hooks.

- [ ] **Step 1: Write the failing test**

Append to `test_measure_reminders.py`, before the `if __name__` line:

```python
class Registration(unittest.TestCase):
    def test_given_the_plugin_hooks_file_when_read_then_both_reminders_are_registered_on_an_existing_script(self):
        config = json.loads((HOOKS / "hooks.json").read_text())
        commands = {}
        for event, groups in config["hooks"].items():
            for group in groups:
                for hook in group.get("hooks", []):
                    if "measure_reminders.py" in hook.get("command", ""):
                        commands[event] = (group.get("matcher"), hook["command"])
        self.assertEqual(set(commands), {"SessionStart", "PostToolUse"})
        self.assertEqual(commands["SessionStart"][0], "startup")
        self.assertEqual(commands["PostToolUse"][0], "Skill|Bash|Write|Edit")
        self.assertTrue(commands["SessionStart"][1].endswith("measure_reminders.py session-start"))
        self.assertTrue(commands["PostToolUse"][1].endswith("measure_reminders.py moment"))
        self.assertTrue((HOOKS / "measure_reminders.py").is_file())
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_reminders -q`
Expected: 1 failure (`set()` is not `{'SessionStart', 'PostToolUse'}`).

- [ ] **Step 3: Register the hooks**

In `plugins/flagrare/hooks/hooks.json`:

- Append to the `description` string: ` (4) measure-impact reminders: one line at session start when measurements are due, and a note to Claude after measurable moments (TDD drafted, ticket picked up, PR opened or merged, contribution logged, release).`
- Add a `SessionStart` key inside `"hooks"`:

```json
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/measure_reminders.py session-start",
            "timeout": 10
          }
        ]
      }
    ],
```

- Add one more entry to the existing `PostToolUse` array:

```json
      {
        "matcher": "Skill|Bash|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/measure_reminders.py moment",
            "timeout": 10
          }
        ]
      }
```

- [ ] **Step 4: Document the reminders in the skill**

In `plugins/flagrare/skills/measure-impact/SKILL.md`, add this section right before `## Rules`:

```markdown
## Reminders

Two plugin hooks bring measuring up without the user having to remember:

- **At session start:** when something is due (a check after launch, a bet with no launch date after 30 days, a recent win with no number), the user sees one line, and you get the list. Bring it up once, at a natural point, never in the middle of their task.
- **After a measurable moment:** a TDD drafted, a ticket picked up, projects proposed, a PR opened or merged, a contribution logged, a release. You get a short note; offer this skill in one line at the end of your reply, unless the work is a small fix, was already measured or skipped, or the run is scheduled.

Each moment is mentioned at most once per session, and skipped work stays silent. To turn all reminders off, set `skills["measure-impact"].reminders` to `false` in `~/.claude/skills/flagrare/config.json`.

The hooks cannot see plain conversation ("I shipped it yesterday"). The first time you run for a user, suggest they add this line to their CLAUDE.md or memory, and do not add it yourself: `When I mention work I finished, shipped or launched, offer /flagrare:measure-impact in one line.`
```

- [ ] **Step 5: Mention it in the README**

In `README.md`, in the paragraph that starts with "`/flagrare:measure-impact` measures what a piece of your work changed", insert this sentence before the last sentence ("Where `/flagrare:impact-timeline` reconstructs impact..."):

```markdown
It reminds you too: one line when a session starts and something is due, and a nudge after a TDD, a PR or a logged win, once per session and never for work you skipped.
```

- [ ] **Step 6: Run everything**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

Run: `python3 -c "import json;json.load(open('plugins/flagrare/hooks/hooks.json'));print('ok')"`
Expected: `ok`.

Run: `echo '{"session_id":"x","tool_name":"Skill","tool_input":{"skill":"flagrare:tdd-writer"}}' | python3 plugins/flagrare/hooks/measure_reminders.py moment; echo "exit $?"`
Expected: one JSON line with `additionalContext`, then `exit 0`.

Run: `grep -rn $'—' plugins/flagrare/hooks plugins/flagrare/skills/measure-impact README.md`
Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add plugins/flagrare/hooks/hooks.json plugins/flagrare/skills/measure-impact/SKILL.md README.md plugins/flagrare/lib/career/tests/test_measure_reminders.py
git commit -m "✨ feat(measure-impact): register the reminder hooks and document them"
```

---

### Task 4: Release

**Files:**
- Modify: `plugins/flagrare/.claude-plugin/plugin.json` (via the script), `CHANGELOG.md`

- [ ] **Step 1: Find the newest tag**

Run: `git fetch --tags && git tag --sort=-v:refname | head -1`
Expected: the latest version (at plan time `v1.57.0`). The new version is the next minor.

- [ ] **Step 2: Bump and write the CHANGELOG entry**

Run: `python3 scripts/bump-version.py <next minor>`. Add at the top of `CHANGELOG.md`, below `# Changelog`:

```markdown
## <version>: <date>

Reminders, so measuring impact doesn't depend on remembering it.

### Improved Skills

- **`/flagrare:measure-impact`, reminders**: the skill measured what your work changed, but only when you thought to ask, and the steps people skip are exactly the before and the after. Now two hooks bring it up:
  - **When a session starts:** one line when something is due, for example "Impact: 1 check due (Reorder button). Ask Claude to measure it when you have a minute." Nothing when nothing is due.
  - **After a measurable moment:** a TDD drafted, a ticket picked up, a PR opened or merged, a win logged, a release. Claude offers it in one line at the end of its reply instead of interrupting.
  - **No nagging:** each moment once per session, skipped work stays silent, small fixes and scheduled runs are left alone, and `reminders: false` in the config turns it all off. A hook error never breaks your session.
```

- [ ] **Step 3: Commit, tag, publish, update**

Run this whole block with the sandbox disabled: it writes outside the working folder and reaches the network.

```bash
git add CHANGELOG.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "🔖 release: v<version>"
git tag -a v<version> -m "v<version>"
git push origin main && git push origin v<version>
awk '/^## <version>/{f=1;next}/^## /{f=0}f' CHANGELOG.md > /tmp/notes.md
gh release create v<version> --title v<version> --notes-file /tmp/notes.md
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

Expected: "Plugin flagrare updated from <old> to <version>".
