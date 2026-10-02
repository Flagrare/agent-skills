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

- `plan --entry-file <path>`: save a new measurement, or update one with the same id. Write the JSON to a file in `$TMPDIR` first and pass its path, because queries contain quotes that break a shell argument (`--entry '<json>'` also works for JSON without quotes). Delete the file afterwards, whether the script accepted it or not. `plan` never changes `checks`, `launch_date` or `created_at`: only `launch` and `check` do.
- `launch --id <id> --launch-date <date>`: set the launch date; creates checks 14 and 42 days later. The measurement must exist: when work launches with nothing saved, `plan` it first from what is known, then `launch`.
- `check --id <id> --due <date> --value "<text>" --verdict worked|didnt_work|cant_tell`: record a check.
- `skip --id <id> --title "<work>" --link <link> --kind ticket|tdd|project|log_entry --reason "<why>"`: record a skip.
- `due`: checks past their date, bets with no launch after 30 days, and contributions-log entries from the last 30 days with no measurement (`--all-wins` for every entry, when the user asks to go through old work).
- `show`: everything saved.

The file's shape is in `<plugin root>/lib/career/STATE.md`.

**One entry per piece of work.** Before `plan`, run `show` and look for an entry with the same `work.link`; when there is one, reuse its `id`, so the same work is never saved twice. Otherwise make a short stable id from the work's title. For a contributions-log entry, set `work.link` to the link written in that log line and `kind` to `log_entry`, so `due` stops listing it.

**When a query is refused** as looking like a credential, never save the secret. If the only trigger is a column named like one (`token`, `password`), save the query with that column described in words, and tell the user why.

## Stages

Decide the stage from what you were given, or take it from the arguments:

| Given | Stage |
|---|---|
| a ticket, a TDD, a project or proposal not built yet | before |
| something shipped with a launch date, or a check from `due` | after |
| a contributions-log entry or past work with no number | past |

Sizes: **quick** (about 5 minutes; steps 1, 2, 4, 6 and 9) for tickets and log entries; **full** (all steps) for TDDs, projects and written-case entries. When the arguments name no size, use quick for tickets and log entries and full otherwise. Small fixes with no user-visible change get `skip` with the reason, and nothing else.

## The method, every time

1. **The work and its kind of impact:** for users or partners, technical (speed, errors, reliability, cost), business (revenue, orders, cost), or for the team (time saved, fewer interruptions). Often more than one.
2. **The number that shows it.** Prefer a number leadership already watches. Run `<plugin root>/lib/career/initiatives.py context --home "$HOME" --today <date>`; when it reports `has_map: true`, read its `priorities` (theme, metric, baseline, target, owner team, the user's lever) and connect to one of them first; name the theme.
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

## Reminders

Two plugin hooks bring measuring up without the user having to remember:

- **At session start:** when something is due (a check after launch, a bet with no launch date after 30 days, a recent win with no number), the user sees one line, and you get the list. Bring it up once, at a natural point, never in the middle of their task.
- **At a measurable moment:** a TDD being written, a ticket being picked up, projects being proposed, a PR opened, a contribution logged: you get a short note; offer this skill in one line at the end of your reply, unless the work is a small fix, was already measured or skipped, or the run is scheduled. When a PR is merged or a release is checked, the note asks you to record the launch date with `launch` instead, so the checks come due on their own.

Each moment is mentioned at most once per session, and skipped work stays silent. To turn all reminders off, set `skills["measure-impact"].reminders` to `false` in `~/.claude/skills/flagrare/config.json`.

The hooks cannot see plain conversation ("I shipped it yesterday"). The first time you run for a user, suggest they add this line to their CLAUDE.md or memory, and do not add it yourself: `When I mention work I finished, shipped or launched, offer /flagrare:measure-impact in one line.`

## Rules

- Never invent a number. Every number has a source, or a confidence level and its reasoning.
- Read-only queries only, and never save a credential in a query (the script refuses).
- Report negative and unclear results as plainly as good ones.
- Do not measure other people's work, except to say how much of a shared result is the user's.

## Credits

The confidence levels and their wording, finding data by category across connected tools, the old value against new value check with its three verdicts, and saving the check so it can be re-run are adapted from pstack (MIT, by Lauren Tan; Claude Code port by Lucas Faria): the `why`, `figure-it-out` and `prove-it-works` skills.
