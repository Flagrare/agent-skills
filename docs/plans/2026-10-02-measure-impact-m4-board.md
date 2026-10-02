# Measure impact, Milestone 4: board card and daily digest line. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan's output. Check with `grep -rn $'\u2014' <files>` (no output means clean).

**Goal:** Show what needs measuring where the user already looks every day: a "Measure" card on the board's Proof tab and one "Measure:" line in `/flagrare:career`'s digest.

**Architecture:** `coordinator.board` gains a `measure` block built from `measurements.due` (the same list the session-start reminder uses), so the board and the digest read one source. A broken `measurements.json` is caught inside that block, so it never blanks the rest of the career panel. The template renders the block as one card; the career skill's digest prints one line from it.

**Tech Stack:** Python `unittest`, the board's single-file HTML template (vanilla JS), Markdown skill text.

**Spec:** `docs/plans/2026-10-02-measure-impact-design.md`, section "Reminders", item 4, and the `career` row of "Hand-offs from existing skills". Milestones 1 and 2 shipped in v1.57.0 to v1.58.1; Milestone 3 ships as v1.59.0 before this plan starts.

## Global Constraints

- No em-dashes; plain words per `lib/career/GLOSSARY.md`; no real company data in fixtures.
- The board only reads; nothing on it measures or writes.
- Card copy names the skill to run (`/flagrare:measure-impact`); it never asks the user to type a raw script command.
- The card works in light and dark mode and at phone width (390px) with no horizontal scroll.
- Commits are gitmoji conventional commits straight to `main`, no AI attribution lines.
- Tests: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`.

## Review Focus

1. **A broken `measurements.json`:** the career panel (promotion, project, proof) must still render; only the Measure card shows the read error.
2. **No measurements yet:** the card must invite the first measurement, not say "nothing due" (which would read as "all done").
3. **Long lists:** a user with many wins with no number gets at most 3 per list and an "and N more" line, never a wall.
4. **Hostile text in titles:** titles and log text come from user files; every value goes through `esc`/`inline`, links through `safeUrl`.
5. **`reminders: false`:** the spec says it turns all reminders off, and the card is reminder item 4, so the card hides and the digest line is left out.
6. **Malformed entries, not just invalid JSON:** a saved check whose `due` is a number must not raise out of `measure()` and blank the career panel.

---

### Task 1: `measure` block in `coordinator.board`

**Files:**
- Modify: `plugins/flagrare/lib/career/coordinator.py`
- Modify: `plugins/flagrare/lib/career/measurements.py`, `plugins/flagrare/hooks/measure_reminders.py`
- Test: `plugins/flagrare/lib/career/tests/test_coordinator.py`

**Interfaces:**
- Consumes: `measurements.due(home, today) -> {"checks_due": [{id,title,due}], "bets_waiting": [{id,title,since}], "unmeasured_wins": [{date,link,text}], "count": int}`; `measurements.load(home)` raises `measurements.CorruptFile`.
- Produces: `coordinator.measure(home, today) -> dict`, either `{"has_measurements": bool, "reminders": bool, **due}` or `{"error": str}`; `board()["measure"]` is that dict. `measurements.reminders_on(home) -> bool`, moved from `hooks/measure_reminders.py`, which now delegates to it.

- [ ] **Step 1: Write the failing tests** (append to `test_coordinator.py`)

```python
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

    def test_given_reminders_off_when_building_board_data_then_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, ".claude/skills/flagrare/config.json", {"skills": {"measure-impact": {"reminders": False}}})
            self.assertFalse(co.board(str(home), "2026-10-01")["measure"]["reminders"])

    def test_given_a_saved_check_with_a_malformed_date_when_building_board_data_then_the_rest_still_builds(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            write(home, f"{CAREER}/measurements.json", [{"id": "x", "work": {"title": "X", "link": "https://example.com/x"}, "stage": "after", "checks": [{"due": 5}]}])
            b = co.board(str(home), "2026-10-01")
            self.assertIn("measurements.json", b["measure"]["error"])
            self.assertEqual(b["promotion"], {"has_map": False})
```

- [ ] **Step 2: Run, expect FAIL** with `KeyError: 'measure'`.

Run: `python3 -m unittest tests.test_coordinator.BoardMeasure -q`

- [ ] **Step 3: Implement** in `coordinator.py`: `import measurements`, and

```python
def measure(home: str, today: str) -> dict:
    """The Measure card and digest line: what is due, from the same list the session-start reminder uses.
    A broken measurements file is reported here, so it never hides the rest of the board."""
    try:
        saved = measurements.load(home)
        return {"has_measurements": bool(saved), "reminders": _reminders_on(home), **measurements.due(home, today)}
    except measurements.CorruptFile as exc:
        return {"error": str(exc)}
    except (TypeError, ValueError, AttributeError) as exc:
        return {"error": f"{measurements.file_path(home)} has an entry that could not be read ({exc})"}
```

Move `reminders_on(home)` and `OFF_VALUES` from `hooks/measure_reminders.py` into `measurements.py` unchanged (it reads `skills["measure-impact"].reminders` from the shared config; a missing or unreadable config means on), and make the hook's `reminders_on` call `_lib()[1].reminders_on(home)`, so there is one copy. `coordinator.measure` uses `measurements.reminders_on`. The 28 hook tests stay the coverage for the values. Add `"measure": measure(home, today)` to `board()`.

- [ ] **Step 4: Run, expect PASS**, then the whole suite.
- [ ] **Step 5: Commit** `✨ feat(career): board data carries what needs measuring`

### Task 2: The Measure card on the Proof tab

**Files:**
- Modify: `plugins/flagrare/lib/career/board/template.html`
- Test: `plugins/flagrare/lib/career/tests/test_board_build.py`

**Interfaces:**
- Consumes: `DATA.career.measure` from Task 1.
- Produces: a `#measure-sec` section at the top of `.proof-side`, shown whenever `DATA.career` has no top-level `error` and `measure.reminders` is not `false`.

- [ ] **Step 1: Failing build test** (the page carries the block, and the template has the card's mount point)

```python
    def test_given_a_check_due_when_building_then_the_page_carries_the_measure_block(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as board:
            career = Path(home) / CAREER
            career.mkdir(parents=True)
            (career / "measurements.json").write_text(json.dumps([{"id": "faster-search", "work": {"title": "Faster search", "link": "https://example.com/t/1", "kind": "ticket"},
                "stage": "after", "created_at": "2026-08-01", "launch_date": "2026-09-01", "checks": [{"after_days": 14, "due": "2026-09-15", "done_at": None}]}]))
            (Path(board) / "data.json").write_text(json.dumps({"scan": {}, "items": []}))
            subprocess.run([sys.executable, str(BOARD / "build.py"), board, "--home", home, "--today", "2026-10-01"], check=True, capture_output=True)
            html = (Path(board) / "board.html").read_text()
            data = json.loads(html.split("/*DATA*/", 1)[1].split("/*END*/", 1)[0])
            self.assertEqual(data["career"]["measure"]["checks_due"][0]["id"], "faster-search")
            self.assertIn('id="measure-sec"', html)
```

- [ ] **Step 2: Run, expect FAIL** on `id="measure-sec"` (the data half already passes after Task 1).
- [ ] **Step 3: Implement.**
  - Markup, first child of `.proof-side`:
    `<section id="measure-sec" aria-labelledby="h-measure" hidden><div class="sec"><h2 id="h-measure"><a class="term" href="#g-measure" data-term="measure">Measure</a></h2><span class="n" id="n-measure"></span></div><div class="box measure" id="measure-body"></div></section>`
  - Glossary: `DEF.measure = "Work whose effect you haven't checked yet: checks due after a launch, bets still waiting for a launch date, and wins in your log with no number. Ask Claude to run /flagrare:measure-impact on one."` and `["Measure", "measure"]` in `GLOSS` after `["The bet", "bet"]`.
  - Render (after the recognition block): `const MEAS = CAREER.measure || {};` and, when `!CAREER.error`:
    - `MEAS.error`: one `.wait-who` line, "Couldn't read your saved measurements: <esc(error)>".
    - `!MEAS.has_measurements && !MEAS.count`: "Nothing measured yet. Before you build something, ask Claude to run <code>/flagrare:measure-impact</code> on it to set its bet."
    - `!MEAS.count`: "Nothing to measure right now."
    - `MEAS.reminders === false`: leave the section hidden.
    - otherwise up to three groups, each an `h4` plus at most 3 `.evi-item` rows and a `.wait-who` "and N more" line: **Checks due** (title, "due <fmt(due)>"), **Bets waiting for a launch date** (title, "bet set <fmt(since)>"), **Wins with no number** (date, link via `safeUrl`, text via `inline`). Under the groups, one `.sec-sub`-sized line: "Ask Claude to measure one with <code>/flagrare:measure-impact</code>."
    - `$("n-measure").textContent = MEAS.count ? String(MEAS.count) : ""`; unhide the section.
  - CSS: `.measure { padding: var(--s-5); display: grid; gap: var(--s-4); }` and `.measure h4` matching `.recog h4`; reuse the existing tokens only.
- [ ] **Step 4: Run, expect PASS**, then the whole suite.
- [ ] **Step 5: Browser check.** Build Yuri's board with the installed-from-repo template (`python3 plugins/flagrare/lib/career/board/build.py ~/Dev/classpass/senior-scan-board --home "$HOME"`), open `http://localhost:8770/board.html#proof`, and screenshot: light, dark (`prefers-color-scheme` emulation), and 390px wide. Also check one fixture board where every list has more than 3 entries. Expected: card first in the right column, no horizontal scroll, "and N more" lines present.
- [ ] **Step 6: Commit** `✨ feat(career): a Measure card on the board's Proof tab`

### Task 3: The "Measure:" line in the career digest

**Files:**
- Modify: `plugins/flagrare/skills/career/SKILL.md` (step 3 template and its Rules)
- Test: `plugins/flagrare/lib/career/tests/test_measure_handoffs.py`

- [ ] **Step 1: Failing contract test**: add `"career": "**Measure:**"` to the wired map that `Handoffs.check` reads.
- [ ] **Step 2: Run, expect FAIL** (text missing).
- [ ] **Step 3: Edit.** In the step 3 opening sentence, add "what needs measuring" to the list `coordinator.py board` returns. In the template, after the `**Promotion:**` line:
  `**Measure:** <checks due, with titles>; <bets waiting for a launch date>; <wins with no number, as a count> (only when measure.count is above 0 and measure.reminders is true)`
  Add a Rules bullet: "**The Measure line** comes from `board.measure`. Leave it out when nothing is due or reminders are off. When `measure.error` is set, put "measurements file unreadable" in the caveat line instead. In an interactive run the closing question may offer to measure one item; a scheduled run only lists them." Add "the Measure line" to the "Cap it" list.
- [ ] **Step 4: Run, expect PASS**, then the whole suite.
- [ ] **Step 5: Commit** `✨ feat(career): the daily digest says what needs measuring`

### Task 4: Release

Check the newest tag, bump to the next minor, narrative CHANGELOG entry (what the user now sees on the board and in the digest, and that a broken measurements file only affects the card), `🔖 release: vX`, annotated tag, push, `gh release create`, local update. Rebuild Yuri's board with the installed version.
