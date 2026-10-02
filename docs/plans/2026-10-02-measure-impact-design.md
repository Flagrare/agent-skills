# Measure impact design: a systematic way to measure the impact of your work

> No em-dashes in this document (repo hook enforces it in generated `.md`).

Status: design, approved section by section on 2026-10-02. Next step: implementation plan.

## Problem

The career skills find work worth doing and record what the user did, but almost nothing in them measures what that work changed. Most entries in a real contributions log read as activity ("reviewed X, found Y"), and a promotion packet is judged by people who don't know the user, from written outcomes.

Three things went wrong in practice when impact was talked about without a method:

- **Arbitrary targets.** A "bet" with a made-up number is a wish. An educated guess needs a measured starting point and a comparison that can be checked.
- **The wrong metric.** For a "report a user" feature, the obvious metric (report volume) turned out to be tiny once it was estimated from real rates: about 0.43 disruptive reports per 10,000 fitness bookings, which predicts under one a week for the new flow. The real value was elsewhere. Only the estimate exposed that.
- **Forgetting.** The steps people skip are measuring before building and checking after launch. Instructions alone don't fix that: in long sessions they get forgotten.

## Goal

A skill, `/flagrare:measure-impact`, that makes the user think about impact the same systematic way every time, at any stage of the work, plus reminders that bring it up when it is feasible, due or worth doing, without nagging.

## Decisions (from the design Q&A)

1. **One skill, three stages:** before (not built yet), after (shipped), past (shipped earlier, never measured). Past work is in scope from the start.
2. **It follows up after launch.** Each measurement is saved with its check dates; the after stage re-runs the saved query.
3. **Reminders come from hooks, not memory alone** (approach B): one at session start when something is due, and one when a measurable moment happens in a session, routed to Claude so it raises it at a natural point.
4. **Other skills hand off to it** instead of computing numbers themselves.
5. **Ideas borrowed, with credit, from pstack** (MIT, Lauren Tan; Claude Code port by Lucas Faria): confidence levels and their wording (from `why`), finding data by category across connected tools (from `why`), old value vs new value with three verdicts (from `figure-it-out`), and saving the check so it can be re-run (from `prove-it-works`).

## The skill

### Stages

| Stage | When | Output |
|---|---|---|
| before | a ticket, TDD or project not built yet | the bet: an educated guess with a baseline, a range and a confidence level, plus the saved query that measures it |
| after | about 2 and 6 weeks after launch | the saved query re-run: old value vs new value, a verdict, and the result as action, measured result, impact |
| past | work already shipped with no number | the best number still findable, with its confidence level, or "Unknown: searched X and Y" |

The skill infers the stage from what it is given (a ticket key or TDD means before, a merged PR with a launch date means after, a contributions-log entry means past), or the user names it.

### The thinking, every time

1. **The work and its kind of impact:** for users or partners, technical, business, or for the team. Often more than one.
2. **The number that shows it.** Prefer one leadership already watches. With a promotion map, read its `priorities` (theme, metric, baseline, target, owner team, the user's lever) and connect to one of them first.
3. **Where the data lives.** Check the connected tools by category: source control, tickets, docs, chat, observability (Datadog, New Relic), errors, product analytics and the data warehouse (Snowflake, BigQuery). Use what is connected; never assume a tool.
4. **The baseline:** today's value, the exact query or link, and the date it was taken. If it cannot be found, say why and how to get it.
5. **A comparable, when there is no direct baseline:** the closest thing that can be measured, scaled by the right base (per booking, venue, order or user), never a raw count.
6. **The range and the confidence level,** with the reasons it could be off.
7. **How much is the user's:** their own work, a team effort, or a contribution to someone else's.
8. **How it will be tracked:** the event, metric or table that shows the change, and whether it exists yet.
9. **The sentence.** Before: "We believe [change] will [result], because [evidence]". After and past: "[action], [measured result], leading to [impact]".

### Confidence levels

Every number and every claim about cause carries one:

- **Direct:** a source states it (a query result, a dashboard value, a written statement).
- **Supported:** several pieces of evidence agree.
- **Inferred:** a reasonable reading of the context; the reasoning is written out.
- **Speculative:** a plausible guess; other explanations fit too.
- **Unknown:** searched, not found; the searches are listed.

Words that claim cause ("because", "fixes", "led to") are only used at Direct or Supported, with the source next to them. Inferred and Speculative use hedged wording ("likely", "suggests", "is consistent with").

### Verdicts (after stage)

Worked, didn't work, or can't tell. "Can't tell" is not a pass, and a negative result is reported, not hidden.

### Sizes

- **Quick (about 5 minutes):** steps 1, 2, 4 and 9. For tickets and log entries.
- **Full:** every step. For TDDs, projects and written-case entries.
- **Skip:** small fixes with no user-visible change are skipped, and the skip is recorded so the same work is never asked about again.

### Hard rules

- Every number has a source, or a confidence level with its reasoning. The skill never invents a number.
- Queries are read-only.
- Plain words, following the career glossary.
- Nothing is posted anywhere. Writing up a result for the user to post follows the same approval rules as every other career skill.

## Saved state

A new file, `~/.claude/skills/flagrare/career/measurements.json`, next to the contributions log. One entry per measured or skipped piece of work:

```json
[{
  "id": "stable-slug",
  "work": { "title": "plain words", "link": "<ticket, TDD, PR or log entry>", "kind": "ticket|tdd|project|log_entry" },
  "stage": "before|after|past|skipped",
  "skipped_reason": "",
  "impact_types": ["partners", "business"],
  "metric": { "name": "...", "why": "...", "priority_theme": "<theme from the map, when any>" },
  "source": { "category": "data warehouse", "tool": "snowflake", "query": "<exact text>", "run_at": "2026-10-02" },
  "baseline": { "value": "...", "as_of": "2026-10-02", "confidence": "direct" },
  "comparable": { "what": "...", "base": "per 10,000 bookings", "value": "...", "confidence": "supported" },
  "bet": { "sentence": "We believe ...", "range": "...", "confidence": "inferred" },
  "ownership": "mine|team|contributed",
  "launch_date": null,
  "checks": [{ "due": "2026-10-19", "done_at": null, "value": null, "verdict": null }],
  "result": { "sentence": "", "confidence": "" }
}]
```

A helper, `lib/career/measurements.py`, follows the career library's rule: it reads and prints planned writes as JSON, and the skill writes the file with the Write tool. Commands:

- `plan` for a new or updated entry (validates stage, confidence levels, ownership and dates; stores the query verbatim).
- `launch` to set the launch date and create the 2 and 6 week checks.
- `check` to record a check's value and verdict.
- `skip` to record a skip with its reason.
- `due --today <date>`: checks past their date, before-stage bets with no launch date after 30 days, and contributions-log entries with no measurement that were not skipped (matched by link).

The shape goes in `lib/career/STATE.md`; the plain names (bet, baseline, check, confidence level) go in `lib/career/GLOSSARY.md`.

## Reminders

1. **Session start (hook).** Runs `measurements.py due`. If anything is due, one line, for example "Impact: 1 check due (report-user, 2 weeks after launch), 3 logged wins with no number." Nothing when nothing is due.
2. **Moments in a session (hook).** After a tool or skill call that marks a measurable moment, a short note goes to Claude (not shown to the user) so it raises the measurement at a natural point, usually one line at the end of a reply. Moments:
   - a `tdd-writer`, `work-prep`/`intake` or `opportunity-scan` run finished;
   - a PR opened or merged (`open-pr`, or `gh pr create` / `gh pr merge`);
   - a new entry written to the contributions log;
   - a release (`release-check`).
3. **Plain conversation.** The skill's description covers "shipped", "launched", "what impact did that have", "self-review", "how do I measure this". A memory rule tells Claude to offer it when the user mentions finished work.
4. **Board and daily digest.** A "Measure" card on the Proof tab (checks due, bets waiting for launch, wins with no number) and one "Measure:" line in `/flagrare:career`'s digest when something is due.

**Noise rules:**

- an item is mentioned at most once per session (the event hook keeps a per-session list in a temp file);
- skipped items stay silent;
- small fixes never trigger anything;
- `skills["measure-impact"].reminders: false` in the shared config turns all reminders off;
- scheduled runs list what is due and never ask.

## Hand-offs from existing skills

Other skills never compute numbers themselves. They call `/flagrare:measure-impact` with the stage, the work's link and a size, and use what it saved.

| Skill | When it calls | What it uses |
|---|---|---|
| `tdd-writer` | while drafting, full, before | the bet and numbers for a short product section at the top; the tracking plan for the monitoring section |
| `work-prep` / `intake` | after reading the ticket, quick, before | a 5-minute bet, or a recorded skip |
| `atdd-plan` | when the measurement says tracking is missing | a plan step to add the event or metric, before the feature |
| `opportunity-scan` | when scoring the impact factor | the educated target and its source; the impact score cites it |
| `open-pr` | when writing the description | one line, "how we'll know this worked", when a bet exists |
| `impact-scan` | after logging a contribution | a quick past-stage measurement of that entry, or a skip |
| `career` | every run | the due list for the digest and the board |
| `brag-doc`, `impact-timeline`, `promotion` (packet mode) | when writing up work | measured results first, as action, result, impact; wins with no number are flagged, never padded |

`ticket-creator` is not wired in (tickets stay short), nor are the code review skills.

## Testing

All fixtures use invented data.

- **`measurements.py`** (unit tests, names describe behavior): saves an entry with its query verbatim; rejects an unknown stage, confidence level or ownership; `launch` creates checks 14 and 42 days after the launch date; `due` lists checks past their date, bets with no launch after 30 days, and log entries with no measurement; skipped entries are never listed; nothing that looks like a secret is written.
- **Hooks:** the session-start hook prints nothing when nothing is due and one line when something is; the event hook mentions an item at most once per session; `reminders: false` silences both; a skipped item stays silent.
- **Skill evals:** the before stage on an invented ticket produces a bet whose numbers carry a source or a confidence level; with no data source reachable it answers "Unknown" and lists what it searched instead of inventing a number; an after check that cannot tell reports "can't tell", not success.
- **Board:** the Measure card renders in light and dark mode and on a phone width, checked in the browser.

## Build order

Each milestone is usable on its own.

1. **The skill and its saved file:** `skills/measure-impact/SKILL.md` (stages, thinking steps, confidence levels, sizes, rules, credit to pstack), `lib/career/measurements.py` with tests, `STATE.md` and `GLOSSARY.md` entries, evals.
2. **Reminders:** the session-start and event hooks in `hooks/hooks.json` with their scripts and tests, and the memory rule text the skill suggests to the user.
3. **Hand-offs:** the edits to the eight skills above.
4. **Board and daily digest:** the Measure card in the board template and `coordinator.py board`, and the "Measure:" line in the career digest.

## Release

The usual process: check the newest tag first (`git fetch --tags && git tag --sort=-v:refname | head -1`), bump with `scripts/bump-version.py`, a narrative CHANGELOG entry, gitmoji commits straight to main, an annotated tag, `gh release create`, then the local update. One release per milestone or one at the end, decided when the build starts.

## Out of scope

- Dashboards or charts of measurements over time.
- Automatic data pulls on a schedule; checks run when the user or the daily career run asks.
- Measuring other people's work.
