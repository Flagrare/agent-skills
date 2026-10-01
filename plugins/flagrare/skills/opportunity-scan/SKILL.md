---
name: opportunity-scan
description: Propose two or three pieces of work the user could own end to end, instead of threads to reply to. It sweeps the org's connected surfaces (chat, tickets, docs, PRs) over the last month for recurring pain, silent degradation, ownership gaps, unanswered invitations and leadership priorities, adds the problems /flagrare:impact-scan handed off, checks that nobody already owns each one, and ranks them against the user's promotion map (what they want more and less of, which open rubric row it closes, who cares and whether they have seen the user's work, whether it can land before the target cycle). Each proposal comes with evidence links, a hypothesis and success metric set before building, the smallest first step, and a short pitch for the manager that fits how the company decides. Keeps at most one initiative active, and only after manager alignment. Runs about monthly. Use when the user says "opportunity scan", "what should I own", "what could I lead", "find me a project", "what problem should I pick up", "what would move the needle", "I want to own something end to end", or asks for work that would show next-level scope. Also trigger from /flagrare:career when the scan is due.
---

# Opportunity Scan

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

Impact-scan finds threads to weigh in on. The next level asks for more: finding a problem nobody assigned, and owning it through to a result someone can measure. This skill looks for those problems on purpose, checks nobody already owns them, and brings back two or three proposals the user could take to their manager.

The failure modes it must never enable:
- **Grabbing someone else's work.** A problem already owned is not an opportunity. The owner check runs before anything is proposed, and a proposal that skipped it is cut.
- **Going around the people who decide.** A proposal fits how the company makes decisions: if a PM drives the decision document, the first step feeds evidence into that document, never a competing one.
- **Pitching on a guess.** Every claim in a proposal has a link, or is marked as a check to run first.
- **Spreading thin.** At most one initiative is active, and it only counts as the user's after their manager agrees.

**This skill never posts, sends, or publishes anything.** Sweeps are read-only, and the pitch is a draft for the user.

## Library and state

Helper scripts live at `<plugin root>/lib/career/`, where the plugin root is two directories above this skill's base directory. Run them as `python3 <plugin root>/lib/career/<script>.py ...`. They only read and print JSON. Write every state file with the Write tool, reading it first if it exists: a sandboxed shell cannot write under `~/.claude/skills`.

- `initiatives.py context --home "$HOME" --today <YYYY-MM-DD>`: everything the ranking reads (see step 1).
- `initiatives.py propose --home "$HOME" --today <date> --id <slug> --title "<plain words>" --evidence <link> [--evidence <link> ...] --proposal '<json>'`: plans `initiatives.json` with a proposal.
- `initiatives.py status --home "$HOME" --today <date> --id <slug> --status <status> [--aligned-with "<who>"] [--note "<why>"]`: plans one status change.
- `initiatives.py run --home "$HOME" --today <date>`: plans `opportunity-state.json` with this run's date.

A script that refuses (exit code 2) prints the reason; tell the user in plain words and do not work around it. The state files' shapes are in `<plugin root>/lib/career/STATE.md`.

## Setup (every run)

1. **Load state.** Run `python3 <plugin root>/lib/career/career_state.py plan --home "$HOME"` and apply each `write` action with the Write tool, reading the target first if it exists. **Never delete anything.**
2. **Config.** Read `~/.claude/skills/flagrare/config.json`. This skill sweeps the same surfaces as impact-scan and reuses its onboarding: surfaces, domains, target behaviors and audience come from `skills["impact-scan"]` (or the older `skills["senior-scan"]`). If neither block has `onboarding_complete: true`, run the onboarding in `<plugin root>/skills/impact-scan/SKILL.md` (identity, career target, domains, surfaces; skip voice and board if the user wants to move on) and save it under `skills["impact-scan"]`. This skill's own block, `skills["opportunity-scan"]`, only holds `cadence_days` (default 30).

## Workflow

### 1. Context and cadence

Run `initiatives.py context`. It prints:

- `has_map`, and from the promotion map: `target` (`target_level`, `cycle`, `why`, `more_of`, `less_of`), `open_rows` (rubric rows not yet done), `unseen_people`, `decision_process` (`artifact`, `usual_driver`), and `packet_deadline`. `more_of` and `less_of` are lists by design; for the single-valued facts (`target_level`, `cycle`, the `decision_process` fields, `packet_deadline`), a list means the map's sources disagree: show every option, never pick one.
- `initiatives`: the `active` one (or null), `proposed`, `candidates` (most seen first) and `dropped` (each with `seen_again`: seen since it was dismissed).
- `cadence`: `last_run`, `days_since`, `due`, and `window_start`, the first day to sweep (the last run, or 30 days back the first time, never more than 90 days back).
- `fallback`: the impact-scan config's `target_behaviors`, `domains` and `audience`.

**Cadence.** When the user asked for this scan, run it even if it is not due. When `/flagrare:career` or a schedule started it and `due` is false, stop and say when it is next due.

**Without a map** the scan still runs. Ranking uses the configured target behaviors and domains; the "which open row" and "before the target cycle" factors are skipped; the first step defaults to bringing the problem to the manager. Say once, in the digest header, that `/flagrare:promotion` would sharpen the ranking.

**With an active initiative**, open the digest with a one-line check-in on it (what the last evidence shows, and whether it looks done). New proposals are still made, but none can become active until the current one is done or dropped.

### 2. Sweep

Spawn **one read-only sweep subagent per configured surface**, all in the same message so they run concurrently, over `window_start` to today. Each gets its surface's scope, the domain map with keywords, the exclusions and the user's identity. Sweeps never post, react or comment.

Every sweep hunts the same five signals:

- **Recurring pain:** the same question asked again, repeat incidents with one cause, support toil, a manual step people keep doing by hand.
- **Silent degradation:** something getting slower, flakier or more expensive with nobody assigned (a flaky test everyone reruns, an alert everyone mutes, a metric trending the wrong way).
- **Ownership gaps:** a new integration or partner nobody supports, a team missing a skill it needs, work orphaned by a reorg or a departure.
- **Unanswered invitations:** "someone should look at this", "would love help with", a proposal waiting for a volunteer.
- **Leadership priorities:** themes documents, OKRs, planning docs, a new leader's stated focus. Search the docs surface for them; they tell you which problems will be noticed.

Each finding comes back as: the problem in plain words, every evidence link, who is affected, who has talked about it, and any sign of an owner (an assignee, a ticket in progress, someone saying "I'm on it").

Add the `candidates` from `initiatives.json` (the problems impact-scan handed off) to the findings, and any `dropped` item with `seen_again: true`, marked as dismissed before.

### 3. Owner check (hard filter)

For every finding, check whether someone already owns it before ranking it:

- search open tickets for the problem's keywords and linked incidents;
- search open PRs touching the systems involved;
- read the latest messages in the thread or channel where it was raised.

Record what you checked in one sentence (it becomes the proposal's `owner_check`). If someone owns it, cut it and name the owner on the digest's **Cut** line; if the owner has gone quiet for weeks, it can stay, as "offer to help or take over", never as the user's own. A finding you could not check is cut too, with the reason.

### 4. Rank

Score each surviving finding 0-2 on six factors:

- **Fit:** it matches what the user wants more of, and is not something they want less of (with no map: their configured target behaviors).
- **Rubric:** it closes one of the `open_rows`; pick the row from `open_rows` only, never invent one (no map: skip, score 1).
- **Who cares:** people who would notice the result, with extra weight when they are in `unseen_people`.
- **Standing:** the user knows the area (one of their domains, systems they have worked in).
- **Evidence:** how often it came up and from how many places; a handed-off candidate with `seen_count` 2 or more starts at 2.
- **Timing:** it can show a result before the `packet_deadline` (no map or no deadline: skip, score 1).

Drop anything scoring 0 on Standing or Evidence. Keep the top 3.

### 5. Proposals

The digest is short: the user should know what each proposal is from its first line.

```
## Opportunity scan: <date>, window <window_start> to <today>. <caveats: surfaces skipped, no map, not due but run on request>
<one line on the active initiative, when there is one>
<Still on the table: each earlier `proposed` item, one line each with its title and when it was proposed, when there are any>

### 1. <the problem in plain words, as the thing to own>
**Evidence:** <links, each with three words on what it shows>
**Owner check:** <what was searched, in one sentence, and who owns it, if anyone>
**Hypothesis:** We believe <change> will <result> because <reason>. **Success:** <metric, measured how, decided before building>. (<rubric row id>, only with a map)
**Rough impact:** <who gets what, in plain words>. **Who cares:** <people or teams, and why now>.
**First step:** <the smallest step, fitted to how decisions are made>
**Pitch for your manager:** <three sentences at most, in the user's voice>

(repeat, at most 3)

**Cut:** <finding: reason (owned by X, could not verify, no standing)>; ...
```

Rules:

- **Fit the local decision process.** When `decision_process.usual_driver` is a PM or product role, the first step feeds evidence to them for their `artifact`, and the pitch offers to own the engineering side. When it names engineering, the first step can be a short written proposal. Without a map, the first step is bringing it to the manager.
- **Nothing on an unchecked claim.** Numbers and causes in a proposal come from a link. When one is missing, write `Check first:` with the single check instead of the claim.
- **The hypothesis comes before the build.** A proposal without a success metric is not ready: say what data would show it worked, and where that data lives.
- **Plain words.** No ticket keys or channel ids in the headline; they go in the evidence links. Rubric row ids go in parentheses after the hypothesis, only with a map.
- **Pitch in the user's voice.** Read `~/.claude/skills/flagrare/career/voice.md` when it exists. First person, no preamble, no flourish.

Earlier proposals the user kept but has not started stay on the "Still on the table" line, not in the three new slots; ask whether any is now agreed with the manager or should be dropped.

Stop after the Cut line. Ask which proposals to keep, which to dismiss, and whether any is already agreed with their manager.

### 6. Record

After the user answers, write each change with the Write tool, one script call at a time (each reads the file the previous one wrote):

- **Keep:** `initiatives.py propose` with the fields below. For a handed-off candidate, reuse its id so its sightings carry over.
- **Dismiss:** for an item already in `initiatives.json` (a handed-off candidate, an earlier proposal, a dismissed problem seen again), `initiatives.py status --status dropped --note "<why, in the user's words>"`; it will not come back unless it is seen again. A new finding from this run that the user dismisses is simply not recorded. A handed-off candidate the user neither keeps nor dismisses stays a candidate and comes back next run.
- **Agreed with the manager:** keep it first (`propose`, if it is not already proposed), then `initiatives.py status --status active --aligned-with "<who>" --note "<where or how it was agreed>"`. Only a proposal can become active, only one at a time, and never without the user saying their manager agreed. Do not suggest skipping that conversation.
- **Finished or abandoned** (when the user says so later): `--status done` or `--status dropped`.
- **Bring back a dismissed problem** that has not been seen again (only when the user asks): `--status candidate` first, then `propose`.

The `--proposal` JSON holds: `problem`, `hypothesis`, `metric`, `impact`, `who_cares`, `why_now`, `first_step`, `pitch`, `owner_check`, `decision_fit` (how the first step fits the decision process), and `rubric_rows` (ids from `open_rows`, empty without a map). The script refuses a proposal missing `problem`, `hypothesis`, `metric`, `first_step`, `pitch` or `owner_check`.

Finally run `initiatives.py run` and write `opportunity-state.json`, even when nothing was kept, so the cadence counts from today. If a write fails, say so: the next scan would re-propose the same things.

When an initiative becomes active, suggest logging its milestones as contributions with `/flagrare:impact-scan` as they land; the contributions log stays the evidence trail.
