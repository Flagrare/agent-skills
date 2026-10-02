---
name: career
description: Run the career skills that are due, in one pass, and return one short combined digest plus an updated board. It reads timestamps and flags to decide: the promotion map's first run when there is none (after asking), a refresh of map sections that are older than 90 days or flagged by a scan, an opportunity scan when the last one is a month old, and an impact scan every time. The digest leads with the initiative the user owns and its next step, then up to 5 threads worth weighing in on, one line on the promotion map (open rubric rows, people who haven't seen the work, when to talk to the manager, the packet deadline), anything that needs the user, and an "all answering, nothing owned" warning when the user keeps replying but owns nothing. A scheduled run (from /loop or a schedule) never asks questions and never posts; it lists what needs the user as pending. Use when the user says "career", "career check", "career digest", "run my career skills", "what should I do for my promotion this week", "daily career scan", or sets up a recurring career run. Also trigger for a scheduled career run.
---

# Career

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

> **Plain words.** In anything the user reads, use the plain names in `<plugin root>/lib/career/GLOSSARY.md` ("Senior behaviors", not "rubric rows"; "your written case", not "packet"; "the project you own", not "initiative"). The first time a term appears, say what it means in a few words and add the company's own word in parentheses when the user will hear it at work.

Four skills share one folder of state (`~/.claude/skills/flagrare/career/`): `/flagrare:promotion` keeps the map of where the user is going, `/flagrare:opportunity-scan` finds work to own, `/flagrare:impact-scan` finds threads to weigh in on, and this skill runs whichever are due and folds their results into one digest and one board. It decides from timestamps and flags, not from a fixed routine, so a daily run is cheap on days when only the impact scan is due.

**This skill never posts, sends, or publishes anything**, and neither do the skills it runs.

## Library

Helper scripts live at `<plugin root>/lib/career/`, where the plugin root is two directories above this skill's base directory. They only read and print JSON; every state file is written with the Write tool. Shapes are in `<plugin root>/lib/career/STATE.md`.

- `coordinator.py due --home "$HOME" --today <YYYY-MM-DD>`: the steps to run, in order, each with `skill`, `mode`, `sections`, `needs_user` and `why`.
- `coordinator.py balance --home "$HOME" --today <date>`: contributions in the last 30 days, the active initiative, and the `warn` flag with its `message`.
- `coordinator.py map --home "$HOME" --today <date>`: the map line (target level, open rubric rows, people who haven't seen the work, the manager-conversation dates, the packet deadline), or `has_map: false`.
- `coordinator.py readiness --home "$HOME" --today <date>`: evidence per rubric row (`strong` 3 or more, `thin` 1 or 2, `empty`).

## Interactive or scheduled

Decide this first, and say it in the digest header.

- **Interactive:** the user started this run in the conversation. Steps that need the user may ask.
- **Scheduled:** the run came from `/loop`, a cron or schedule, or a prompt that says it runs unattended. **Never ask a question, never wait for an answer, never post.** Every step with `needs_user: true` is skipped and listed under "Needs you", except a promotion refresh, which still runs for the sections that need no answer (see step 2). Steps that only read and propose still run.

## Workflow

### 1. Load state

Run `python3 <plugin root>/lib/career/career_state.py plan --home "$HOME"` and apply each `write` action with the Write tool, reading the target first if it exists. **Never delete anything.** Then run `coordinator.py due`.

### 2. Run what is due, in order

Run each step by invoking that skill with the Skill tool, passing `called by /flagrare:career, <interactive|scheduled>, <mode>, sections: <sections>` as its arguments. Each skill's own rules still apply (its owner checks, its hard filters, its approval gate for drafts). Ask each one to return its digest without its closing question; this skill asks once at the end.

- **`promotion`, `first_run`** (no map): interactive, ask once: "Full promotion setup now (it is long and saves as it goes), or just today's scans with your current config?" Run the first run only on yes. On no, save today's date as `skills.career.promotion_setup_declined_at` in `config.json` and do not ask again for 30 days (list it under Needs you instead). Scheduled: skip it and list it under Needs you.
- **`promotion`, `resume` or `refresh`:** run the refresh (or the resume of an interrupted first run) of exactly the listed `sections`. In a scheduled run with `needs_user` true, still call promotion: it re-researches the sections that need no answer and returns the rest (target, people, manager questions) as lines for Needs you. A scheduled `resume` goes under Needs you whole, since the remaining phases start with questions.
- **`opportunity-scan`:** due when the last one is 30 days old (or its configured cadence), not merely because nothing is owned: the balance warning covers that. It records its proposals as candidates and the run date before returning, so the next run is not due again tomorrow. Turning a proposal into the user's initiative needs the user and their manager, so a scheduled run lists the proposals under Needs you.
- **`impact-scan`:** every run. A scheduled run keeps its drafts in the digest and the board; nothing is sent.

If a step fails (a missing MCP, a failed write, a script error), keep going with the next one and put the failure in the caveat line.

### 3. Combined digest

Run `coordinator.py board` (the active initiative with its proposal, the proposals on the table, the candidates still waiting for the user's decision, the map line, readiness per rubric row, the balance check, and what needs measuring, in one call), then write one digest. It replaces the separate digests of the skills it ran: do not repeat them in full.

```
## Career: <date>, <interactive|scheduled>. Ran: <skills>. <caveats: failed steps, surfaces skipped, no map>

**The project you own:** <title>: <its next step, from proposal.first_step or the latest evidence> (or "none yet", plus the top proposed project when there is one)

| # | What's going on | What you'd do | Why it matters | Next step |
|---|---|---|---|---|
<up to 5 rows from the impact scan, same rules as its table>

**Promotion:** <N> of <total> Senior behaviors not shown yet (<the ones with little proof, by label>); haven't seen your work yet: <names>; talk to your manager by <comfortable_by> (latest <absolute_by>); written case due <date> (<status>).
**Measure:** check due: <up to 3 titles, then "and N more">; waiting for a launch date: <same>; <N> wins with no number
**Needs you:** <each pending interactive step, one line with why>
**Heads up:** <balance message, only when warn is true>
```

Rules:

- **Cap it.** Initiative line, at most 5 table rows, one map line, one Measure line, the Needs you list, the warning. Item blocks with drafts follow the table only for rows that have a draft, in the impact-scan item format. Opportunity proposals appear as one line each under Needs you or the initiative line, with a pointer to the full proposals ("run /flagrare:opportunity-scan to see them in full").
- **The table follows impact-scan's rules:** plain product language, no ticket keys or row ids in cells, verb-first actions, a next step in every row.
- **The Measure line** comes from `measure` in the board data. Print it only when `count` is above 0 and `reminders` is not false, and omit any empty group (no "check due:" when nothing is due). When `measure.error` is set, put "measurements file unreadable" in the caveat line instead; when `measure.problems` is not empty, add "<N> saved measurements could not be read" there. Interactive: the closing question may offer to measure one of them with `/flagrare:measure-impact`; scheduled: only list them.
- **The map line marks inferred dates as inferred**, and when the map has no people, rubric or calendar yet, it says which part is missing instead of guessing.
- **The "lots of answering, nothing owned" warning lives only here.** Show it when `warn` is true, in the script's words, and add one sentence on what would fix it (the top proposal, or running an opportunity scan).
- **Without a map** the map line reads "No promotion map yet: run /flagrare:promotion to build one", and the first-run question goes under Needs you in a scheduled run.

Interactive: end with one question: which rows to act on, which proposals to keep or dismiss (recorded with opportunity-scan's step 6), and anything under Needs you to do now. Scheduled: end after the last line.

### 4. Board

Rebuild the board once, after everything else: update `<board dir>/data.json` with the impact scan's items, reading it first and keeping the items already there that are `waiting` or `done` (the impact-scan skill describes the shape), then run `python3 <plugin root>/lib/career/board/build.py <board dir> --home "$HOME"`. The board dir is `skills.career.board.dir` in `~/.claude/skills/flagrare/config.json` (or `skills["senior-scan"].board.dir`). The build adds the rest on its own, from the career folder:
- the initiative card, including the candidates awaiting the user's decision;
- the promotion panel, with deadline countdowns;
- the packet readiness panel (from the map's `packet_readiness`);
- evidence per rubric row by `label`, with the three biggest gaps and each row's `next_step`;
- a sparkline of contributions logged per week over the last eight weeks;
- the Recognition card (from `career/recognition.json`, when a recognition tool is set up): totals, company values, who recognized the user most, and the latest thanks.

The page also has search and filters, foldable panels, keyboard shortcuts, "new since your last visit" marks and "Tell Claude" buttons that copy a sentence for the user to paste into chat; impact-scan describes how to handle those sentences.

The page itself warns when its scan is two or more days old. If no board folder is configured: interactive, ask once where it should live (default `~/career-board`) and save it as `skills.career.board.dir`; scheduled, skip the board and say so in the caveat line. If the sandbox blocks the write, rerun the build outside it; if the build fails, say so in the caveat line.

## Setting up a recurring run

When the user asks for a daily or weekly career run, suggest `/loop` or a scheduled task with the prompt "run /flagrare:career (scheduled)", and explain that it will never ask or post, and will list anything that needs them under Needs you.
