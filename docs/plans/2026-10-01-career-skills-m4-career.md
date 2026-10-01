# Career skills, Milestone 4: the career coordinator (as built)

> No em-dashes in this document (repo hook).

**Goal:** Ship `/flagrare:career`, which runs whichever career skills are due and folds them into one capped digest and one board, plus the board's initiative card and promotion panel. Ships as 1.47.0.

**Spec:** `docs/plans/2026-09-30-career-skills-design.md`, sections `career` (coordinator) and Board, Milestone 4, and acceptance tests 5 and 6.

**How it was built:** the user asked for the remaining milestones to run to the end without stopping to ask. Every file was written and tested in a scratch copy of the library first (114 tests). They then landed in five commits straight from that copy, followed by one whole-release review on the most capable model. There was no subagent per task: the content was already complete and tested, and per-task round trips had become the slow part.

## Architecture

The same split as the other career skills applies: the library reads state and decides mechanically, and the skill text decides how to run each step.

`lib/career/coordinator.py` is read-only and has five commands:
- `due`: the steps of a run, in order, from the map's missing and stale sections, `flags.json`, and the opportunity-scan cadence. Each step carries `needs_user`.
- `balance`: the "all answering, nothing owned" check. It warns at 3 or more contributions in 30 days with no active initiative.
- `readiness`: evidence per rubric row, counting log entries tagged with the row plus the row's own evidence. The states are `strong` (3+), `thin` (1-2) and `empty`.
- `map`: the digest's map line.
- `board`: what `build.py` embeds for the board.

The other skills learn when the coordinator calls them:
- They return their digest without the closing question.
- In a scheduled run they never ask.
- A scheduled opportunity scan keeps its findings as candidates, so the next interactive scan can propose them.

## Decisions

- **Opportunity-scan is due on its cadence only** (also noted in the spec's career table). The spec's table says "no active initiative, or last opportunity-scan more than 30 days ago". With no active initiative, the first half would re-run the scan on every daily career run, which contradicts the skill's own monthly cadence. The balance warning covers "nothing owned" instead.
- **`needs_user` rules:**
  - A promotion first run or an interrupted first run always needs the user.
  - A refresh needs the user only when it touches `target` or `people`, the sections that are confirmed with the user.
  - In a scheduled run, promotion is still called for such a refresh and returns what needs the user as Needs you lines; a scheduled resume of an interrupted first run goes to Needs you whole.
- **The open draft-rules item from the spec** (every chat draft ends with its link; every claim hedged) is resolved:
  - Impact-scan now gives the link when a draft is saved into the chat tool.
  - Hedging and tone stay in each user's `voice.md`, which already wins over the generic drafting floor.
  - The spec carries a note to that effect.
- **Board:** the board is renamed "Career Board". It opens with the initiative the user owns, or what is on the table plus the balance warning. It adds a promotion panel, and counts evidence per open rubric row when there is a map; otherwise it counts by configured behavior, as before. `build.py` takes `--today` (defaulting to the scan date).
- **Carried from the Milestone 3 reviews into `initiatives.py`:**
  - a last run dated in the future counts as today;
  - a cadence written as text is coerced, with the default as fallback;
  - a blank manager name is refused on activation.
- **`STATE.md`** names the required proposal fields and states where notes are kept.

## Commits

1. `ab7dd01` ✨ coordinator library and cadence hardening (`coordinator.py`, `initiatives.py`, tests: 94 to 112).
2. `01cf11a` ✨ Career Board (`build.py`, `template.html`, tests: 112 to 114).
3. `65dfde5` ✨ coordinator hooks in impact-scan, opportunity-scan and promotion; `STATE.md`; spec note.
4. `663ac67` ✨ the career skill, evals and fixtures.
5. `2002bbc` 📝 README (thirty-seven skills, coordinator paragraph); `e426aa6` 🔖 release v1.47.0.
6. `501141c` 🐛 fixes from the whole-release review. Each problem below, and what changed:
   - **Opportunity-scan under the coordinator never recorded anything,** so interactive career runs would repeat the monthly sweep. It now records each undecided proposal as a candidate (one sighting, reusing existing ids) and the run date in both modes, and career's closing question asks about proposals.
   - **Impact-scan's paragraph read as skipping its `scan-state.json` write.** It now keeps step 6.
   - **Scheduled refreshes that touched `target` or `people`:** a scheduled run still calls promotion, which researches the rest and returns the user lines. `manager_questions` joins `NEEDS_USER`.
   - **The digest had no documented source for its lines.** It now reads `coordinator.py board` in one call.
   - **The board:**
     - no board folder: ask in an interactive run, skip with a caveat in a scheduled one;
     - `waiting` and `done` items are kept;
     - inferred dates are marked;
     - one definition of "thin";
     - a malformed map no longer breaks the build, which renders without the career panel and warns.
   - **A declined promotion setup** is not asked again for 30 days.
   - **The balance window** is exactly 30 days.
   - **Evals** state today's date.
7. A last docs commit for the re-review's wording notes: the scheduled refresh exception, the explicit `opportunity-state.json` write, and the eval wording.

## Parked

- Corrupt state files are replaced wholesale, and malformed map or config shapes can raise. This is the same family as the earlier milestones.
- The validator does not check that required fact paths exist.
- The eval runner's support for fixture `files` is still unverified. The fixtures are there for graders and humans.
