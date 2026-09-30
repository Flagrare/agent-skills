# Career skills, Milestone 2a: rename senior-scan to impact-scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan or anything it produces (repo hook). Check with `python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" <files>`, which must print 0. Never run `scripts/check-no-emdash.py` by hand (it reads hook JSON from stdin and hangs).

**Goal:** Rename `/flagrare:senior-scan` to `/flagrare:impact-scan`, move its state into the shared `career/` folder with a merge that loses nothing, move the board into the shared library, and fix every reference, with no change to how the scan finds, scores or drafts items. Ships as 1.44.0.

**Architecture:** Milestone 2 is split. 2a (this plan) is mechanical: the rename, the state location, the board move, and a shared state doc. 2b (the next plan, 1.45.0) changes behavior: map-aware scoring, staleness flags, the recurring-problem hand-off, and rubric-row tagging. The library stays plan-only except `board/build.py`, which writes `board.html` into the user's own board folder (it already did that before the move).

**Tech Stack:** Markdown skills, Python 3 stdlib, `unittest`.

**Spec:** `docs/plans/2026-09-30-career-skills-design.md` (Milestone 2). Deviations, recorded as rulings in the execution ledger:
- **The board moves to `plugins/flagrare/lib/career/board/`**, not `skills/career/board/`. `career` has no `SKILL.md` until Milestone 4, and Milestone 1 already put shared code in `lib/career/`.
- **The log's rubric-row tag is an additive trailing field** `| row: <id>`, instead of replacing the `behavior:` value. This keeps the board's evidence-coverage panel working, since it matches on `behavior:` text. 2a only teaches readers to accept the field; 2b starts writing it.
- **`scan-state.json` and `voice.md` are merged on every load-state run**, not copied once. Senior-scan kept writing the old files after Milestone 1 shipped.

## Global Constraints

- No em-dashes in any file. Verify with the command above.
- Python: stdlib only, `from __future__ import annotations`, system `python3`. No pip installs.
- Tests: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v` from the repo root. Expected total after this plan: 44.
- Library scripts never write under `~/.claude/skills/`. Only `board/build.py` writes, and only `board.html` in the board folder it is given.
- Shared state folder: `~/.claude/skills/flagrare/career/`. Legacy folder: `~/.claude/skills/flagrare/senior-scan/`. Never delete anything in either.
- Skills reference the library relative to the plugin root (two directories above the skill's base directory), never by absolute path.
- Commits go directly to `main`, gitmoji plus conventional, no attribution lines. The release commit and tag stay local until the user approves publishing.

## Review Focus

1. **A user kept running senior-scan after installing 1.43.0**, so career `scan-state.json` is older than legacy `state.json`. The merge must keep the later `last_run` and every seen item (Task 1).
2. **The same item is in both states with different statuses.** `contributed` must win, or the scan re-surfaces work the user already did (Task 1).
3. **Existing boards.** A board built from the moved script must show every entry from both logs (Task 2). The user's existing board folder, configured under `skills["senior-scan"].board.dir`, must still be found (Task 4 text).
4. **Both skills triggering on the same phrase.** The deprecated stub's description carries no trigger phrases (Task 4).
5. **Old free-text log lines and new `| row:` lines mixed.** The parser keeps both (Task 2).

---

## File Structure

```
plugins/flagrare/lib/career/
  career_state.py            # modify: merge scan-state.json and voice.md (Task 1)
  STATE.md                   # create: shapes of every career state file (Task 3)
  board/
    template.html            # moved from skills/senior-scan/board/ (Task 2)
    build.py                 # rewritten in place of skills/senior-scan/board/build.py (Task 2)
  tests/
    test_career_state.py     # modify (Task 1)
    test_board_build.py      # create (Task 2)
plugins/flagrare/skills/
  impact-scan/SKILL.md       # renamed from senior-scan, rewritten (Task 4)
  senior-scan/SKILL.md       # deprecated stub (Task 4)
  impact-timeline/SKILL.md   # modify line 51 (Task 4)
  promotion/SKILL.md         # add STATE.md pointer (Task 3)
README.md, CHANGELOG.md, plugins/flagrare/.claude-plugin/plugin.json   # Task 5
```

---

### Task 1: Merge scan state and voice on every load

**Files:**
- Modify: `plugins/flagrare/lib/career/career_state.py`
- Modify: `plugins/flagrare/lib/career/tests/test_career_state.py`

**Interfaces:**
- Consumes: `paths`, `_read` and `plan_migration` from Milestone 1.
- Produces:
  - `plan_migration(home)` also plans a merged `scan-state.json`: the later `last_run`, the union of `seen` by `id`, with `contributed` winning.
  - It also plans a newer-wins `voice.md`.
  - New private helpers: `_merge_seen`, `_plan_scan_state`, `_plan_voice`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_career_state.py`, replace this existing test. It expected "never touch career state", which is no longer the rule:

```python
    def test_given_existing_career_state_when_planning_then_does_not_overwrite_it(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", '{"old": true}')
            write(home, f"{CAREER}/scan-state.json", '{"new": true}')
            paths = [a["path"] for a in cs.plan_migration(str(home))]
            self.assertFalse(any(p.endswith("scan-state.json") for p in paths))
```

with:

```python
    def test_given_existing_career_state_when_planning_then_keeps_career_values(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", '{"old": true}')
            write(home, f"{CAREER}/scan-state.json", '{"new": true}')
            writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("scan-state.json")]
            merged = json.loads(writes[0]["content"])
            self.assertTrue(merged["new"])
            self.assertTrue(merged["old"])

    def test_given_career_log_with_structure_when_planning_then_preserves_format(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            career_text = "# h\n\n- a\n  continuation line\n## notes\n\n- d\n"
            legacy_text = "# h\n\n- a\n- b\n"
            write(home, f"{LEGACY}/contributions.log.md", legacy_text)
            write(home, f"{CAREER}/contributions.log.md", career_text)
            actions = cs.plan_migration(str(home))
            log_writes = [a for a in actions if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            content = log_writes[0]["content"]
            self.assertIn("## notes", content)
            self.assertIn("  continuation line", content)
            self.assertIn("- b", content)
            lines = content.split('\n')
            notes_idx = next((i for i, l in enumerate(lines) if l == "## notes"), -1)
            cont_idx = next((i for i, l in enumerate(lines) if "continuation" in l), -1)
            b_idx = next((i for i, l in enumerate(lines) if l == "- b"), -1)
            self.assertGreater(notes_idx, -1)
            self.assertGreater(cont_idx, -1)
            self.assertGreater(b_idx, notes_idx)

    def test_given_legacy_with_paragraph_when_planning_then_copies_verbatim(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            legacy_text = "# h\n\nSome intro text.\n\n- a\n- b\n"
            write(home, f"{LEGACY}/contributions.log.md", legacy_text)
            actions = cs.plan_migration(str(home))
            log_writes = [a for a in actions if a["path"].endswith("contributions.log.md")]
            self.assertEqual(len(log_writes), 1)
            self.assertEqual(log_writes[0]["content"], legacy_text)
```

and insert these two classes directly above `class Config(unittest.TestCase):`:

```python
class ScanStateMerge(unittest.TestCase):
    def _plan_state(self, home: Path) -> dict:
        writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("scan-state.json")]
        return json.loads(writes[0]["content"]) if writes else {}

    def test_given_legacy_state_newer_when_planning_then_merge_takes_later_last_run_and_all_items(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps({"last_run": "2026-10-05T10:00:00Z", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}, {"id": "b", "status": "surfaced", "surfaced_at": "2026-10-05"}]}))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30T10:00:00Z", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-09-30"}]}))
            merged = self._plan_state(home)
            self.assertEqual(merged["last_run"], "2026-10-05T10:00:00Z")
            self.assertEqual([i["id"] for i in merged["seen"]], ["a", "b"])

    def test_given_career_marks_item_contributed_when_merging_then_contributed_wins(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/state.json", json.dumps({"last_run": "2026-10-05", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}]}))
            write(home, f"{CAREER}/scan-state.json", json.dumps({"last_run": "2026-09-30", "seen": [{"id": "a", "status": "contributed", "surfaced_at": "2026-09-30"}]}))
            self.assertEqual(self._plan_state(home)["seen"][0]["status"], "contributed")

    def test_given_states_already_merged_when_planning_then_no_state_write(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            state = {"last_run": "2026-10-05", "seen": [{"id": "a", "status": "surfaced", "surfaced_at": "2026-10-05"}]}
            write(home, f"{LEGACY}/state.json", json.dumps(state))
            write(home, f"{CAREER}/scan-state.json", json.dumps(state))
            self.assertEqual(self._plan_state(home), {})


class VoiceCopy(unittest.TestCase):
    def test_given_legacy_voice_newer_and_different_when_planning_then_copies_it(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/voice.md", "old rules")
            write(home, f"{LEGACY}/voice.md", "new rules")
            os.utime(home / CAREER / "voice.md", (1_000_000, 1_000_000))
            writes = [a for a in cs.plan_migration(str(home)) if a["path"].endswith("voice.md")]
            self.assertEqual(writes[0]["content"], "new rules")

    def test_given_career_voice_newer_when_planning_then_keeps_it(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{LEGACY}/voice.md", "legacy rules")
            write(home, f"{CAREER}/voice.md", "edited rules")
            os.utime(home / LEGACY / "voice.md", (1_000_000, 1_000_000))
            self.assertFalse([a for a in cs.plan_migration(str(home)) if a["path"].endswith("voice.md")])


```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL in `ScanStateMerge`, `VoiceCopy` and `keeps_career_values`, because there is no merged write yet.

- [ ] **Step 3: Implement**

In `career_state.py`, replace the loop that copies `state.json` and `voice.md`:

```python
    for legacy_name, target_key in (("state.json", "scan_state"), ("voice.md", "voice")):
        source = _read(legacy / legacy_name)
        if source is not None and not Path(p[target_key]).is_file():
            actions.append({"action": "write", "path": p[target_key], "content": source, "reason": f"copy {legacy_name} from senior-scan"})
```

with:

```python
    actions += _plan_scan_state(legacy / "state.json", Path(p["scan_state"]))
    actions += _plan_voice(legacy / "voice.md", Path(p["voice"]))
```

and add these helpers directly above `def skill_config(`:

```python
def _merge_seen(legacy: list, career: list) -> list:
    """Union of seen items by id. A contributed item wins; otherwise the later surfaced_at wins."""
    merged: dict[str, dict] = {}
    order: list[str] = []
    for item in (legacy or []) + (career or []):
        key = item.get("id")
        if key is None:
            continue
        if key not in merged:
            merged[key] = item
            order.append(key)
            continue
        current = merged[key]
        if current.get("status") == "contributed" and item.get("status") != "contributed":
            continue
        if item.get("status") == "contributed" and current.get("status") != "contributed":
            merged[key] = item
            continue
        if str(item.get("surfaced_at", "")) >= str(current.get("surfaced_at", "")):
            merged[key] = item
    return [merged[k] for k in order]


def _plan_scan_state(legacy_path: Path, career_path: Path) -> list[dict]:
    """Copy or merge senior-scan's state.json into career/scan-state.json, never losing a seen item."""
    legacy_text = _read(legacy_path)
    if legacy_text is None:
        return []
    career_text = _read(career_path)
    if career_text is None:
        return [{"action": "write", "path": str(career_path), "content": legacy_text, "reason": "copy state.json from senior-scan"}]
    try:
        legacy_state = json.loads(legacy_text)
        career_state = json.loads(career_text)
    except json.JSONDecodeError:
        return []
    merged = {**legacy_state, **career_state}
    if "last_run" in legacy_state or "last_run" in career_state:
        merged["last_run"] = max(str(legacy_state.get("last_run") or ""), str(career_state.get("last_run") or ""))
    if "seen" in legacy_state or "seen" in career_state:
        merged["seen"] = _merge_seen(legacy_state.get("seen", []), career_state.get("seen", []))
    if merged == career_state:
        return []
    content = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
    return [{"action": "write", "path": str(career_path), "content": content, "reason": "merge newer senior-scan state into career scan-state"}]


def _plan_voice(legacy_path: Path, career_path: Path) -> list[dict]:
    """Copy voice.md when missing, or when the legacy copy is newer and different."""
    legacy_text = _read(legacy_path)
    if legacy_text is None:
        return []
    career_text = _read(career_path)
    if career_text is None:
        return [{"action": "write", "path": str(career_path), "content": legacy_text, "reason": "copy voice.md from senior-scan"}]
    if legacy_text != career_text and legacy_path.stat().st_mtime > career_path.stat().st_mtime:
        return [{"action": "write", "path": str(career_path), "content": legacy_text, "reason": "legacy voice.md is newer"}]
    return []
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 41 tests.

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/lib/career
git commit -m "✨ feat(impact-scan): merge senior-scan state and voice into career on every load"
```

---

### Task 2: Move the board into the shared library

**Files:**
- Move: `plugins/flagrare/skills/senior-scan/board/template.html` to `plugins/flagrare/lib/career/board/template.html`
- Delete: `plugins/flagrare/skills/senior-scan/board/build.py`
- Create: `plugins/flagrare/lib/career/board/build.py`
- Test: `plugins/flagrare/lib/career/tests/test_board_build.py`

**Interfaces:**
- Consumes: `career_state.read_contributions(home)`.
- Produces:
  - The command `python3 <plugin root>/lib/career/board/build.py <board_dir> [--home HOME]`.
  - `parse_contributions(lines) -> list[dict]`, with keys `id, date, link, title, what, behavior, row`. `row` is `None` when the line has no `| row:` field.

- [ ] **Step 1: Move the template and remove the old script**

```bash
mkdir -p plugins/flagrare/lib/career/board
git mv plugins/flagrare/skills/senior-scan/board/template.html plugins/flagrare/lib/career/board/template.html
git rm -q plugins/flagrare/skills/senior-scan/board/build.py
```

- [ ] **Step 2: Write the failing test**

```python
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BOARD = Path(__file__).resolve().parents[1] / "board"
sys.path.insert(0, str(BOARD))
import build  # noqa: E402

LEGACY = ".claude/skills/flagrare/senior-scan"
CAREER = ".claude/skills/flagrare/career"


class ParseContributions(unittest.TestCase):
    def test_given_old_free_text_entry_when_parsing_then_keeps_behavior_and_no_row(self):
        [c] = build.parse_contributions(["- 2026-09-30 | https://x | fixed a thing | behavior: unblocking others"])
        self.assertEqual(c["behavior"], "unblocking others")
        self.assertIsNone(c["row"])

    def test_given_entry_with_row_field_when_parsing_then_reads_both(self):
        [c] = build.parse_contributions(["- 2026-09-30 | https://x | fixed a thing | behavior: unblocking others | row: scope.proactive-discovery"])
        self.assertEqual(c["behavior"], "unblocking others")
        self.assertEqual(c["row"], "scope.proactive-discovery")


class Build(unittest.TestCase):
    def test_given_legacy_and_career_logs_when_building_then_board_shows_entries_from_both(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            for rel, text in ((f"{LEGACY}/contributions.log.md", "# h\n\n- 2026-09-29 | https://a | legacy only | behavior: x\n"),
                              (f"{CAREER}/contributions.log.md", "# h\n\n- 2026-09-30 | https://b | career only | behavior: y | row: r.one\n")):
                p = Path(home) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            (Path(board) / "data.json").write_text(json.dumps({"scan": {}, "items": []}))
            subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home], check=True, capture_output=True)
            page = (Path(board) / "board.html").read_text()
            self.assertIn("legacy only", page)
            self.assertIn("career only", page)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run it to verify it fails**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build'`.

- [ ] **Step 4: Write `plugins/flagrare/lib/career/board/build.py`**

```python
#!/usr/bin/env python3
"""Render the career board.

Usage: python3 build.py <board_dir> [--home HOME]

Reads <board_dir>/data.json and the contributions log (the union of the
career and legacy senior-scan logs), embeds both into template.html (next to
this script), and writes <board_dir>/board.html. The board folder is the
user's own; this is the only file the library writes.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import career_state  # noqa: E402

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect width='32' height='32' rx='7' fill='%232c5b87'/%3E"
        "%3Ccircle cx='16' cy='16' r='10' fill='none' stroke='white' stroke-width='2.5'/%3E"
        "%3Ccircle cx='16' cy='16' r='5' fill='none' stroke='white' stroke-width='2.5'/%3E"
        "%3Ccircle cx='16' cy='16' r='1.8' fill='%23f0b35c'/%3E%3C/svg%3E")
ENTRY = re.compile(r"- (\d{4}-\d{2}-\d{2}) \| (\S+) \| (.+?) \| behavior: (.+?)(?: \| row: (\S+))?$")


def link_title(link: str) -> str:
    pr = re.search(r"github\.com/[^/]+/([^/]+)/pull/(\d+)", link)
    if pr:
        return f"{pr.group(1)} #{pr.group(2)}"
    ticket = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", link)
    if ticket:
        return ticket.group(1)
    if "slack.com" in link:
        return "Slack thread"
    if "notion." in link:
        return "Notion page"
    return "Link"


def parse_contributions(lines: list[str]) -> list[dict]:
    """Log entries as board records. The trailing `| row: <id>` field is optional."""
    out = []
    for i, line in enumerate(lines):
        m = ENTRY.match(line.strip())
        if m:
            date, link, what, behavior, row = m.groups()
            out.append({"id": f"c{i}", "date": date, "link": link, "title": link_title(link),
                        "what": what, "behavior": behavior, "row": row})
    return out


def render(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    template = (HERE / "template.html").read_text(encoding="utf-8")
    body = re.sub(r"/\*DATA\*/.*?/\*END\*/", lambda _: "/*DATA*/" + payload + "/*END*/", template, flags=re.S)
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<link rel="icon" type="image/svg+xml" href="{html.escape(ICON)}">'
            '<style>:root{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>'
            '</head><body>' + body + '</body></html>')


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the career board.")
    parser.add_argument("board_dir")
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    board = Path(args.board_dir).expanduser()
    data = json.loads((board / "data.json").read_text(encoding="utf-8"))
    data["contributions"] = parse_contributions(career_state.read_contributions(args.home))
    out = board / "board.html"
    out.write_text(render(data), encoding="utf-8")
    print(f"wrote {out}: {len(data.get('items', []))} items, {len(data['contributions'])} contributions")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 44 tests.

- [ ] **Step 6: Commit**

```bash
git add plugins/flagrare/lib/career plugins/flagrare/skills/senior-scan
git commit -m "♻️ refactor(impact-scan): move the board into lib/career and read both contribution logs"
```

---

### Task 3: Shared state reference and promotion pointer

**Files:**
- Create: `plugins/flagrare/lib/career/STATE.md`
- Modify: `plugins/flagrare/skills/promotion/SKILL.md` (section `## Library`)

- [ ] **Step 1: Write `STATE.md`**

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
  "seen": [{ "id": "slack:C123:1790703452.608029", "source": "slack", "surfaced_at": "2026-09-30T13:30:00Z", "status": "surfaced|contributed|dropped" }] }
```

When both the old and new files exist, the merge keeps the later `last_run` and the union of `seen` by `id`; a `contributed` item wins over any other status for the same id. Other top-level keys are kept.

## voice.md

The user's observed writing rules, used for drafts. The newer of the old and new copies wins.

## promotion-map.json and promotion-map.md

Written only by `/flagrare:promotion`. Shape: `skills/promotion/reference/map-schema.md`.

## flags.json

Signals that part of the promotion map may be stale. Other skills append; `/flagrare:promotion` reads them on refresh and removes the ones it handled.

```json
[{ "section": "org", "reason": "the consumer director is leaving", "source": "<link>", "raised_at": "2026-09-30" }]
```

`section` is one of the promotion map's sections (`target`, `process`, `calendar`, `rubric`, `org`, `people`, `precedent`, `packet_readiness`, `manager_questions`).

## initiatives.json

Work the user could own. Candidates can come from impact-scan (a problem seen more than once); `/flagrare:opportunity-scan` ranks them. At most one item is `active`.

```json
[{ "id": "stable-slug", "title": "plain words", "evidence": ["<link>"], "seen_count": 2,
   "first_seen": "2026-09-25", "last_seen": "2026-09-30", "status": "candidate|proposed|active|done|dropped" }]
```
````

- [ ] **Step 2: Point promotion at it**

In `plugins/flagrare/skills/promotion/SKILL.md`, section `## Library`, find the sentence "The map's shape is in `reference/map-schema.md`, and the markdown layout is in `reference/map-template.md`." Add this new sentence after it, in the same paragraph:

"The other shared state files (contributions log, flags, initiatives) are described in `<plugin root>/lib/career/STATE.md`; clear a handled flag by writing `flags.json` back without it."

- [ ] **Step 3: Verify and commit**

```bash
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/lib/career/STATE.md plugins/flagrare/skills/promotion/SKILL.md
git add plugins/flagrare/lib/career/STATE.md plugins/flagrare/skills/promotion/SKILL.md
git commit -m "📝 docs(career): shared state file reference for the career skills"
```

---

### Task 4: Rename the skill, add the stub, fix impact-timeline

**Files:**
- Rename: `plugins/flagrare/skills/senior-scan/` to `plugins/flagrare/skills/impact-scan/`
- Rewrite: `plugins/flagrare/skills/impact-scan/SKILL.md`
- Create: `plugins/flagrare/skills/senior-scan/SKILL.md` (stub)
- Modify: `plugins/flagrare/skills/impact-timeline/SKILL.md:51`

- [ ] **Step 1: Rename**

```bash
git mv plugins/flagrare/skills/senior-scan plugins/flagrare/skills/impact-scan
ls plugins/flagrare/skills/impact-scan
```
Expected: only `SKILL.md`, because the board moved in Task 2.

- [ ] **Step 2: Write the new `plugins/flagrare/skills/impact-scan/SKILL.md`**

This is the complete file. It starts with `---` on line 1.

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

## Setup (first run only)

Config lives in the shared **`~/.claude/skills/flagrare/config.json`**: skill-agnostic keys (GitHub login, display name, repo scope) at the top level, impact-scan keys under `skills["impact-scan"]`. This skill was called senior-scan: when `skills["impact-scan"]` is missing, read `skills["senior-scan"]` instead, and write any changes back under `skills["impact-scan"]`. Mutable files live in **`~/.claude/skills/flagrare/career/`** (`scan-state.json`, `contributions.log.md`, `voice.md`), shared with the other career skills and outside the plugin tree so they survive plugin updates. Their shapes are in `<plugin root>/lib/career/STATE.md`, where the plugin root is two directories above this skill's base directory. The user's **board** (a local HTML dashboard of open items and the evidence log, see workflow step 7) lives wherever `skills.career.board.dir` points, falling back to `skills["senior-scan"].board.dir`.

Write these files (and `config.json`) with the Write tool, never from Bash: a sandboxed Bash cannot write under `~/.claude/skills`, and a failed state write silently breaks dedupe across runs. Reading them from Bash is fine; expand `~` explicitly as `$HOME`.

**Load state first, every run.** Run `python3 <plugin root>/lib/career/career_state.py plan --home "$HOME"` and apply each `write` action with the Write tool, reading the target first if it exists (the Write tool will not overwrite a file it has not read). This brings over, or merges in, anything still in the old `senior-scan/` folder: the contributions log keeps every entry, the scan state keeps every seen item. A `mkdir` action needs no separate step. **Never delete anything.**

If `onboarding_complete` is not `true` in the impact-scan block (or the senior-scan block it falls back to), run onboarding. Reuse any top-level keys another flagrare skill already collected (ask only for what's missing), and only write the `skills["impact-scan"]` block (plus `skills.career.board`) and missing top-level keys; leave other skills' blocks untouched.

### Onboarding

The interview is half discovery, half confirmation: propose from real data wherever possible so the user is confirming lists, not composing them from memory.

1. **Identity.** GitHub login (detect via `gh api user --jq '.login'` or the GitHub MCP `get_me`, confirm) and repo scope (`org:<name>`, `user:<login>`, or explicit `owner/repo` list). Chat handle: look the user up with the chat MCP's user search, confirm the match.
2. **Career target.** Ask current level and target level, then which next-level behaviors to hunt for. Offer defaults by transition and let the user edit or paste their company ladder's actual language:
   - toward **senior**: influence beyond assigned tickets, unblocking others, owning technical decisions in their domain, raising the quality bar
   - toward **staff**: cross-team leverage, setting direction, connecting efforts that don't know about each other, derisking big decisions early
   The chosen behaviors become the definition of the Stretch axis (see Scoring), so they should be concrete.
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

Read `career/scan-state.json` (`{ "last_run": iso8601, "seen": [{ "id", "source", "surfaced_at", "status" }] }`). The scan window is `last_run` to now; if no state exists, default to the last 48 hours, capped at 7 days. Items already in `seen` are only re-surfaced if they escalated: a new decision point, a new unanswered question, a thread reopened.

### 2. Sweep in parallel

Spawn **one read-only sweep subagent per configured surface**, all in the same message so they run concurrently. Each gets its surface's scope, the domain map with keywords, the exclusions, the user's identity (so their own posts are skipped), and the time window.

Every sweep hunts the same four signals: (a) a decision still being formed (architecture, API contracts, migrations, process); (b) a question nobody has answered well, or a thread going in circles; (c) a discussion inside the user's domains that is missing context the user has; (d) work from other teams that touches systems the user owns or depends on. And every sweep returns the same shape, raw findings only, no ranking: location and link, participants, a 2-3 sentence summary, matched signal(s), and the specific gap the user could fill.

**Chat sweep (reference: Slack).** Read recent activity in each configured channel, follow interesting threads, and additionally run 2-3 keyword searches from the domain map, since relevant discussions happen outside configured channels. Ignore social chatter, resolved threads, FYI-only announcements, and threads where the right people are already converging.

**Code-review sweep (reference: GitHub).** List open PRs in the configured repos updated within the window and not authored by the user, then read the promising ones including review threads. Also hunt for: PRs whose changed paths touch the user's domains, and approaches carrying a risk the discussion hasn't caught, judged against the domain map's known failure modes. Ignore approved-and-converging PRs, trivial changes, and PRs where requested changes are simply in progress.

**Generic sweep (any other surface: docs, tickets, other chat platforms).** Enumerate items in scope updated within the window (pages, tickets, threads), read the ones with active human discussion, and apply the four signals. On docs surfaces, treat unresolved comment threads and open review periods on RFCs and design docs as prime candidates: they are decisions with explicit windows. Ignore items with no discussion, resolved threads, and pure status updates.

### 3. Score and cut

Score each candidate 0-2 on five axes:

- **Leverage**: would weighing in change the outcome, or just add a voice? A decided thread scores 0.
- **Credibility**: does the user have specific knowledge, context, or ownership the participants lack? Generic "good point" opinions score 0.
- **Stretch**: does this exercise one of the configured target behaviors, beyond the user's assigned lane? Routine work in their own tickets scores low.
- **Audience**: will configured audience people (or their equivalents) see the contribution? Defaults to 1 when no audience is configured.
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
| 2 | A restaurant got no email or text for two app orders on 9/24; Andrea asked in the [squad channel](<permalink>) whether it should have, nobody answered | Tell her which email should have fired and whether it did | A partner missed real orders, support is stuck · unblocking others | Check first: look the order up in Braze |

### 1. <same verb-first action>
<one sentence: what is happening and where it stands>. <one sentence: why you, naming the fact or context only you bring>.
> <draft, at most 3 sentences>

(repeat per item)

**Cut:** <near-miss, reason>; <near-miss, reason>; ...
```

Rules that keep it scannable:

- **"What's going on" gives the context before the ask.** One plain sentence, 25 words at most: whose thing it is, what it is in product terms, and where it stands (unreviewed, approved, question unanswered since Tuesday). "Diego's [peak-times PR](url) promises a fallback message when loading fails; two people approved it", not "pf #8025 fallback". The thing's name carries the link, so there is no separate Where column.
- **The table speaks product, not code.** No PR numbers, ticket keys, channel ids, function names, or flags in any table cell: a reader cannot decode `ignoreInternalError on #8051` without the context they don't have. Say what breaks for whom ("a server error shows the full-page error screen instead of the retry button"). Code identifiers and `file:line` belong in the item block and the draft, where the reader is already acting.
- **Actions start with a verb and name the move in plain words**: "Point out that a server error blanks the page instead of showing the retry", not "Flag missing `ignoreInternalError` on #8051", and not "Item report error handling".
- **Re-listing follows the same rules.** When remaining items are shown again later in the session, rebuild each row from scratch for a cold reader; never shorten a row to "the same gap" or "item 1's issue" because it was discussed earlier.
- **"Why it matters" says what changes if the user acts, then the behavior it exercises.** The impact is 12 words at most, the concrete outcome ("stops a 502 blanking a page before launch", "a modifiers decision is being made without the person who designed them"), never the score or a restatement of the action. After a `·`, name the configured target behavior in two or three words ("quality bar", "unblocking others"). Rows are ordered by score, so this column is what explains the ranking.
- **Every item ends in a next step.** Either a draft ready to send, or `Check first:` with the single concrete check (a query, a code path to trace) that would make a draft safe. Never a draft built on a claim that has not been verified.
- **No field labels in item blocks** ("What's happening:", "Why you:", "Suggested angle:"). The two sentences and the draft carry all of it.
- **Evidence goes inside the draft, not before it.** If the draft already cites `file:line`, the block does not repeat it.
- **Near misses fit on one line.** A short reason each, so the filter stays honest and tunable without adding a section.
- **Stop after the cut line.** No closing summary. Ask only which items to act on.

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
- <date> | <link> | <one sentence: what the contribution was and what it changed> | behavior: <target behavior exercised>
```

This log is the promotion evidence trail, the lagging indicator made legible. When the user later runs `/flagrare:brag-doc` or builds a promo packet, point them at it; brag-doc should treat it as a first-class source.

Every log entry is also a board update: rebuild so the evidence log shows it, and move the item to `waiting` (a reply is expected) or `done`.

### 7. Keep the board current

The board is the expected output of every scan, not an extra: a local page the user opens to see what to act on next, what is waiting on someone else, and the evidence log. The digest is read once; the board is what they come back to. It is display-only: `data.json` is the single source of truth, the user tells you in chat what changed, and you update the file and rebuild.

**First scan, or no board yet.** If no board directory is configured (including users onboarded before the board existed) or the folder has no `data.json`, create it at the end of this run: ask for the location once (default `~/career-board`), save it as `skills.career.board.dir`, write `data.json` from this scan, build, and tell the user how to open it. Never finish a scan with no board and no caveat saying why.

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
    "why": "Impact in 12 words or less", "behavior": "raising the quality bar",
    "draft": "ready-to-send text", "draft_where": "GitHub inline comment on file.js:60",
    "check_first": "the one check that makes a draft safe",
    "waiting_on": "Eric", "since": "2026-09-29"
  }]
}
```

- `status`: `todo` (shown in the ranked list), `waiting` (raised, waiting on someone; set `waiting_on` and `since`, and after 3 days the board suggests a nudge), `done`, `dropped`.
- `urgency`: `today` (could merge or close before the user acts), `week`, `later`. `deadline` says why.
- `behaviors`: the configured target behaviors; the board shows evidence coverage for each.
- An item carries either `draft` or `check_first`, never a draft built on an unverified claim. The same product-language rules as the digest table apply to `action`, `context` and `why`.
- Keep ids stable across runs. Before adding an item, check for an existing one about the same thread: update it instead of adding a duplicate, and if the new scan contradicts its text, fix the text or flag the conflict to the user.

````

- [ ] **Step 3: Write the stub `plugins/flagrare/skills/senior-scan/SKILL.md`**

````markdown
---
name: senior-scan
description: Deprecated alias for /flagrare:impact-scan.
---

# Senior Scan (renamed)

This skill is now `/flagrare:impact-scan`. Run `/flagrare:impact-scan` instead; it reads the same config and brings over your existing scan state, contributions log and voice rules without deleting anything.
````

- [ ] **Step 4: Fix impact-timeline**

In `plugins/flagrare/skills/impact-timeline/SKILL.md`, replace the opening of line 51:

"If `~/.claude/skills/flagrare/senior-scan/contributions.log.md` exists, read it once before the loop: `/flagrare:senior-scan` appends dated, already-vetted contributions there"

with:

"If `~/.claude/skills/flagrare/career/contributions.log.md` exists (or, on setups that have not run a career skill yet, `~/.claude/skills/flagrare/senior-scan/contributions.log.md`), read it once before the loop: `/flagrare:impact-scan` (formerly senior-scan) appends dated, already-vetted contributions there"

Leave the rest of the line unchanged. `brag-doc` has no reference to the log (verified with grep), so it does not change.

- [ ] **Step 5: Verify and commit**

```bash
python3 -c "t=open('plugins/flagrare/skills/impact-scan/SKILL.md').read();assert t.startswith('---\nname: impact-scan\n');print('ok')"
python3 -c "t=open('plugins/flagrare/skills/senior-scan/SKILL.md').read();assert 'senior scan' not in t.lower().split('---')[1];print('stub-ok')"
grep -rn -e "senior-scan/board" -e "flagrare/senior-scan/contributions" plugins README.md | grep -v "or, on setups" || echo "no-stale-refs"
python3 -c "import sys;print(sum(open(f).read().count(chr(0x2014)) for f in sys.argv[1:]))" plugins/flagrare/skills/impact-scan/SKILL.md plugins/flagrare/skills/senior-scan/SKILL.md plugins/flagrare/skills/impact-timeline/SKILL.md
git add -A plugins/flagrare/skills
git commit -m "✨ feat(impact-scan): rename senior-scan to impact-scan with shared career state and a deprecated alias"
```
Expected: `ok`, `stub-ok`, `no-stale-refs`, `0`.

---

### Task 5: README, CHANGELOG and local release 1.44.0

**Files:** `README.md`, `CHANGELOG.md`, `plugins/flagrare/.claude-plugin/plugin.json`

- [ ] **Step 1: README**

Replace the paragraph that starts with "`/flagrare:senior-scan` scans your org" with this paragraph, in the same position:

"`/flagrare:impact-scan` (formerly `/flagrare:senior-scan`, which still works as an alias) scans your org's communication surfaces for openings to operate at the next level, decisions still being formed, people stuck or circling, discussions missing context only you have, cross-team changes touching systems you own. One read-only sweep agent per surface (chat, code review, docs and tickets, chosen at onboarding from the MCPs actually connected) feeds a five-axis score (leverage, credibility, stretch, audience, timing) behind a hard anti-performative filter: no leverage or no credibility kills an item no matter how visible the thread, because shallow drive-bys hurt the promotion case they were meant to build. Output is a max-5 digest with fully contextualized items and draft replies in your own voice (distilled from your real messages at onboarding), gated behind per-message approval. Posted contributions append to an evidence log in the shared `~/.claude/skills/flagrare/career/` folder that `/flagrare:brag-doc`, `/flagrare:impact-timeline` and `/flagrare:promotion` read. Every scan also keeps a local board current (open items ranked by urgency, what is waiting on whom, and the evidence log), created on the first run and rebuilt whenever an item changes."

- [ ] **Step 2: Tests**

Run: `python3 -m unittest discover -s plugins/flagrare/lib/career/tests -v`
Expected: PASS, 44 tests.

- [ ] **Step 3: Commit the README**

```bash
git diff README.md | python3 -c "import sys;print(sum(l.count(chr(0x2014)) for l in sys.stdin if l.startswith('+')))"
git add README.md
git commit -m "📝 docs(readme): impact-scan replaces senior-scan in the catalog"
```

- [ ] **Step 4: Version and CHANGELOG**

```bash
python3 scripts/bump-version.py 1.44.0
python3 -c "import json;print(json.load(open('plugins/flagrare/.claude-plugin/plugin.json'))['version'])"
```
Expected: `1.44.0`.

Insert at the top of `CHANGELOG.md`, under `# Changelog` and its blank line, above `## 1.43.0`:

```markdown
## 1.44.0: 2026-09-30

Same scan, new name, one shared place for your evidence.

### Improved Skills

- **`/flagrare:impact-scan`, senior-scan renamed and moved into the career family**: the scan now sits beside `/flagrare:promotion` and shares its state instead of keeping a private folder. Field-tested the hard way: the day promotion shipped, senior-scan kept writing its own dedupe state and evidence log while promotion read copies made that morning, so the two drifted within hours. Impact-scan now keeps everything in `~/.claude/skills/flagrare/career/`, and every run merges in whatever is still in the old `senior-scan/` folder without deleting it: the evidence log keeps every entry, the dedupe state keeps the later run and every seen item (an item you already contributed to stays contributed), and the newer voice rules win. Config is read from `skills["impact-scan"]` with the old `skills["senior-scan"]` block as a fallback, and your existing board folder keeps working. `/flagrare:senior-scan` still runs as a deprecated alias. Finding, scoring and drafting are unchanged in this release.

### Tooling

- **Shared career library**: the board template and build script moved to `lib/career/board/`, and the build now reads both the new and the old evidence logs, so no entry disappears during the move. A new `lib/career/STATE.md` documents every shared state file, including the optional `| row: <id>` log field that the next release starts writing. `/flagrare:impact-timeline` reads the evidence log from its new home, with the old path as a fallback.

```

- [ ] **Step 5: Local release commit and tag (do not push)**

```bash
git diff CHANGELOG.md | python3 -c "import sys;print(sum(l.count(chr(0x2014)) for l in sys.stdin if l.startswith('+')))"
git add CHANGELOG.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "🔖 release: v1.44.0"
git tag -a v1.44.0 -m "release v1.44.0" HEAD
```
The controller asks the user before `git push`, pushing the tag, `gh release create` and `/flagrare:update`.
