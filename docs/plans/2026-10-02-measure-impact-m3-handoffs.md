# Measure impact, Milestone 3: hand-offs from other skills. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> No em-dashes anywhere in this plan's output. Check with `grep -rn $'\u2014' <files>` (no output means clean).

**Goal:** Make the skills that sit at measurable moments hand off to `/flagrare:measure-impact` instead of working out numbers themselves, and make the write-up skills lead with measured results.

**Architecture:** Text edits to ten `SKILL.md` files, each at one named anchor, using the hand-off contract Milestone 1 defined: `/flagrare:measure-impact <before|after|past> <link> <quick|full> called by /flagrare:<skill>`, and `measurements.py show` for reading saved results. One contract test reads each wired `SKILL.md` and fails if its hand-off text disappears, so later edits cannot silently unwire a skill. `career` (the daily digest) is Milestone 4 with the board.

**Tech Stack:** Markdown skill files, Python `unittest`.

**Spec:** `docs/plans/2026-10-02-measure-impact-design.md`, section "Hand-offs from existing skills". Milestones 1 and 2 shipped in v1.57.0 to v1.58.1.

## Global Constraints

- No em-dashes; plain words per `lib/career/GLOSSARY.md`; no real company data.
- Each skill only calls the skill or reads `measurements.py show`; none computes or invents a number.
- `ticket-creator` and the code review skills are not wired in (tickets stay short).
- Commits are gitmoji conventional commits straight to `main`, no AI attribution lines.
- Tests: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`.

## Review Focus

1. **An anchor that moved** since this plan was written: the edit must land at the right spot or stop; never append blindly at the end of a file. Each task checks its anchor exists exactly once before inserting.
2. **Double prompting:** work-prep runs intake; intake must not also suggest measuring when called by work-prep (its line says so).
3. **A user with no measurements file:** open-pr, brag-doc, impact-timeline and promotion read `measurements.py show`, which returns `[]`; each must then simply leave the measured line out.
4. **Friction after logging a win:** impact-scan's past measurement must be skippable in one word, or it becomes a nag.
5. **atdd-plan without a bet** must add nothing (its new item says so).

---

### Task 1: Before building: tdd-writer, work-prep, intake, atdd-plan

**Files:**
- Modify: `plugins/flagrare/skills/tdd-writer/SKILL.md`
- Modify: `plugins/flagrare/skills/work-prep/SKILL.md`
- Modify: `plugins/flagrare/skills/intake/SKILL.md`
- Modify: `plugins/flagrare/skills/atdd-plan/SKILL.md`
- Create: `plugins/flagrare/lib/career/tests/test_measure_handoffs.py`

**Interfaces:**
- Consumes: the `/flagrare:measure-impact` arguments contract and `measurements.py show` (Milestone 1).
- Produces: the hand-off text the contract test checks.

- [ ] **Step 1: Write the failing test**

Create `plugins/flagrare/lib/career/tests/test_measure_handoffs.py`:

```python
from __future__ import annotations
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / "skills"


class Handoffs(unittest.TestCase):
    def check(self, wired: dict[str, str]) -> None:
        for name, phrase in wired.items():
            with self.subTest(skill=name):
                text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(phrase, text)

    def test_given_the_skills_used_before_building_when_read_then_each_hands_off_to_measure_impact(self):
        self.check({
            "tdd-writer": 'called by /flagrare:tdd-writer',
            "work-prep": 'called by /flagrare:work-prep',
            "intake": '`/flagrare:measure-impact` can set the bet',
            "atdd-plan": 'bet from `/flagrare:measure-impact`',
        })


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_handoffs -q`
Expected: failures, one per skill not yet wired.

- [ ] **Step 3: Make the edits**

For each edit, first confirm the anchor appears exactly once in the file (`grep -c`); if not, stop and re-anchor.

In `plugins/flagrare/skills/tdd-writer/SKILL.md`, insert this block immediately before the anchor line `### Phase 2: Draft Structure`:

````markdown
### Phase 1.5: Set the bet

Before drafting, run `/flagrare:measure-impact` with `before <ticket, doc or initiative link> full called by /flagrare:tdd-writer`. Use what it returns in two places: the **For product** paragraph at the top of the Introduction (the bet, the number it should move with today's value and its source, how sure we are, what is out of scope), and the Analytics or Observability section (how the change will be tracked). When it reports a baseline as unknown, keep that visible in the doc ("baseline unknown: <how to get it>") instead of inventing a number.
````

In `plugins/flagrare/skills/tdd-writer/SKILL.md`, insert this block immediately after the anchor `## Introduction`:

````markdown
### For product
[3 to 5 plain sentences a product manager can read without the rest of the doc: what changes for users, the bet from /flagrare:measure-impact (the number it should move, today's value and its source, how sure we are), and what is out of scope.]
````

In `plugins/flagrare/skills/work-prep/SKILL.md`, insert this block immediately before the anchor line `### Step 2: Invoke `/flagrare:atdd-plan``:

````markdown
### Step 1.5: Set the bet

Once the brief is complete, run `/flagrare:measure-impact` with `before <ticket link> quick called by /flagrare:work-prep`. A small fix with nothing users notice gets a recorded skip and nothing else. Otherwise pass its bet sentence, the number with its source, and any missing tracking into `/flagrare:atdd-plan`'s opening context, so the plan can add the tracking before the feature.
````

In `plugins/flagrare/skills/intake/SKILL.md`, insert this text as new line(s) right after the line that starts with the anchor `1. **Overview**: 4-6 lines:`:

````markdown
   When the ticket changes something users notice and intake was not called by `/flagrare:work-prep`, add one line to the overview: `/flagrare:measure-impact` can set the bet (the number this should move, from what) before planning.
````

In `plugins/flagrare/skills/atdd-plan/SKILL.md`, insert this text as new line(s) right after the line that starts with the anchor `2. **Name the design patterns** for any non-trivial structural decisions`:

````markdown
3. When the opening context carries a bet from `/flagrare:measure-impact` whose tracking does not exist yet, add the event or metric as an early step and one acceptance test that it records the change. Without a bet, add nothing.
````

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

Run: `git diff | grep '^+' | grep -c $'\u2014'`
Expected: `0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/skills plugins/flagrare/lib/career/tests/test_measure_handoffs.py
git commit -m "✨ feat(measure-impact): before building skills hand off to measure-impact"
```

---

### Task 2: Shipping and scans: open-pr, opportunity-scan, impact-scan

**Files:**
- Modify: `plugins/flagrare/skills/open-pr/SKILL.md`
- Modify: `plugins/flagrare/skills/opportunity-scan/SKILL.md`
- Modify: `plugins/flagrare/skills/impact-scan/SKILL.md`
- Modify: `plugins/flagrare/lib/career/tests/test_measure_handoffs.py`

**Interfaces:**
- Consumes: the `/flagrare:measure-impact` arguments contract and `measurements.py show` (Milestone 1).
- Produces: the hand-off text the contract test checks.

- [ ] **Step 1: Write the failing test**

Add this method to the `Handoffs` class in `test_measure_handoffs.py`:

```python
    def test_given_the_shipping_and_scans_skills_when_read_then_each_hands_off_to_measure_impact(self):
        self.check({
            "open-pr": "How we'll know",
            "opportunity-scan": 'called by /flagrare:opportunity-scan',
            "impact-scan": 'called by /flagrare:impact-scan',
        })
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_handoffs -q`
Expected: failures, one per skill not yet wired.

- [ ] **Step 3: Make the edits**

For each edit, first confirm the anchor appears exactly once in the file (`grep -c`); if not, stop and re-anchor.

In `plugins/flagrare/skills/open-pr/SKILL.md`, insert this text as new line(s) right after the line that starts with the anchor `- **Testing:** What you did to convince yourself it works`:

````markdown
- **How we'll know (only when a bet exists):** run `python3 <plugin root>/lib/career/measurements.py show --home "$HOME"` (the plugin root is two directories above this skill's base directory) and look for the entry whose `work.link` is this PR's ticket or TDD. When there is one, add one sentence: the number this should move, from what, and when it gets checked. When there is none, leave the line out; never invent a number.
````

In `plugins/flagrare/skills/opportunity-scan/SKILL.md`, insert this text as new line(s) right after the line that starts with the anchor `- **Impact (`impact`, x2):**`:

````markdown
  Size it with `/flagrare:measure-impact` (`before <the problem's strongest link> quick called by /flagrare:opportunity-scan`): its baseline, or its comparable scaled by the right base, with the confidence level, is the impact reason. A baseline it reports as unknown scores 0 here and carries its `Check first:`.
````

In `plugins/flagrare/skills/impact-scan/SKILL.md`, insert this text as new line(s) right after the line that starts with the anchor `This log is the promotion evidence trail`:

````markdown
Right after logging, run `/flagrare:measure-impact` with `past <the log line's link> quick called by /flagrare:impact-scan`, unless the user says to skip it. It saves the number the win already carries, or a recorded skip, so the win does not come back as "no number" in the reminders.
````

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

Run: `git diff | grep '^+' | grep -c $'\u2014'`
Expected: `0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/skills plugins/flagrare/lib/career/tests/test_measure_handoffs.py
git commit -m "✨ feat(measure-impact): shipping and scans skills hand off to measure-impact"
```

---

### Task 3: Write-ups: brag-doc, impact-timeline, promotion

**Files:**
- Modify: `plugins/flagrare/skills/brag-doc/SKILL.md`
- Modify: `plugins/flagrare/skills/impact-timeline/SKILL.md`
- Modify: `plugins/flagrare/skills/promotion/SKILL.md`
- Modify: `plugins/flagrare/lib/career/tests/test_measure_handoffs.py`

**Interfaces:**
- Consumes: the `/flagrare:measure-impact` arguments contract and `measurements.py show` (Milestone 1).
- Produces: the hand-off text the contract test checks.

- [ ] **Step 1: Write the failing test**

Add this method to the `Handoffs` class in `test_measure_handoffs.py`:

```python
    def test_given_the_write_ups_skills_when_read_then_each_hands_off_to_measure_impact(self):
        self.check({
            "brag-doc": '### 8b. Measured results',
            "impact-timeline": '**Saved measurements**',
            "promotion": 'results saved by `/flagrare:measure-impact`',
        })
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest tests.test_measure_handoffs -q`
Expected: failures, one per skill not yet wired.

- [ ] **Step 3: Make the edits**

For each edit, first confirm the anchor appears exactly once in the file (`grep -c`); if not, stop and re-anchor.

In `plugins/flagrare/skills/brag-doc/SKILL.md`, insert this block immediately before the anchor line `### 9. Recognition from peers`:

````markdown
### 8b. Measured results

Run `python3 <plugin root>/lib/career/measurements.py show --home "$HOME"`. For work in the window that has a measurement (match by `work.link` against the PRs, tickets and log entries you collected), lead with its result sentence (action, measured result, impact) and keep its confidence level and source next to it. Work without a measurement is described as what was done, never given a number it does not have; when it matters for a review packet, suggest `/flagrare:measure-impact` past for it.
````

In `plugins/flagrare/skills/impact-timeline/SKILL.md`, insert this text as a new line right before the line that starts with the anchor `1. **The company data platform.**`:

````markdown
0. **Saved measurements** (`python3 <plugin root>/lib/career/measurements.py show --home "$HOME"`): results the user already measured with `/flagrare:measure-impact`, each with its query, date and confidence level. Use them first, and re-run their saved queries for the window when the data platform is reachable.
````

In `plugins/flagrare/skills/promotion/SKILL.md`, append this text to the end of the line that starts with the anchor `3. Write each project as action, then measurable result, then impact.`:

````markdown
 Use the results saved by `/flagrare:measure-impact` first (`measurements.py show`), with their confidence levels. For a project with no measurement, run `/flagrare:measure-impact` past for it before writing it up, and keep "unknown" visible rather than inventing a number.
````

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd plugins/flagrare/lib/career && python3 -m unittest discover -s tests -q`
Expected: `OK`.

Run: `git diff | grep '^+' | grep -c $'\u2014'`
Expected: `0`.

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/skills plugins/flagrare/lib/career/tests/test_measure_handoffs.py
git commit -m "✨ feat(measure-impact): write-ups skills hand off to measure-impact"
```

---

### Task 4: Release

- [ ] **Step 1:** `git fetch --tags && git tag --sort=-v:refname | head -1`; the new version is the next minor (at plan time 1.59.0).
- [ ] **Step 2:** `python3 scripts/bump-version.py <version>` and add a CHANGELOG entry below `# Changelog`:

```markdown
## <version>: <date>

Measuring impact is now part of the flow, not a separate chore.

### Improved Skills

- **The skills that sit at measurable moments now hand off to `/flagrare:measure-impact`** instead of guessing numbers themselves:
  - **Before building:** `/flagrare:tdd-writer` sets the bet and opens every TDD with a short "For product" paragraph; `/flagrare:work-prep` sets a quick bet (or records a skip for small fixes) and passes missing tracking to `/flagrare:atdd-plan`, which adds it before the feature.
  - **Shipping and scans:** `/flagrare:open-pr` adds one "how we'll know" line when a bet exists; `/flagrare:opportunity-scan` sizes the impact factor from a measured baseline; `/flagrare:impact-scan` measures a win right after logging it, skippable in one word.
  - **Write-ups:** `/flagrare:brag-doc`, `/flagrare:impact-timeline` and `/flagrare:promotion` (packet mode) lead with measured results and their confidence, and never give a win a number it doesn't have.
```

- [ ] **Step 3:** with the sandbox disabled: commit `🔖 release: v<version>`, annotated tag, push main and the tag, `gh release create` with the entry as notes, then `bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)`.
