# Career skills design: promotion, opportunity-scan, impact-scan, career

> No em-dashes in this document (repo hook enforces it in generated `.md`).

Status: design, approved section by section on 2026-09-30. Next step: implementation plan.

## Problem

`/flagrare:senior-scan` finds threads worth weighing in on, and it does that well. But one long working session showed the scan covers the smallest part of the job. Most of the value came from work nothing automates:

- Finding out how promotions actually work at the company: the process, the calendar, the packet template, and the rubric managers rate against.
- Mapping the org: who sits above each team, and which changes are coming.
- Finding who has first-hand knowledge of the user's work, and who still needs to see it.
- Asking the user what they actually want, and why. That answer (peace of mind, a terminal level, more user-facing work) changed every piece of advice.
- Proposing work the user could own, not just threads to reply to. The Senior rubric's core line is "proactively discovers and solves problems", and nothing in the plugin does that on purpose.

That session also exposed failure modes the skills must guard against:

- **Stale or conflicting sources:** Notion and Miro disagreed on a reporting line, and a director's departure had already been announced.
- **Summarising fetch tools paraphrasing quotes.**
- **Promotion announcements overstating what engineers originated:** figures like "+2.8pp" and "0%" existed in no source.
- **A process doc's prose contradicting the ladder spreadsheet it summarises.**

## Decisions (from the design Q&A)

1. The strategy output is **one markdown promotion map that feeds a dashboard**, plus a JSON copy for other skills.
2. **One unified board.** The existing senior-scan board is extended, not duplicated.
3. **The "who knows your work" list is evidence first, then confirmed by the user.**
4. **The target step asks four things:** level, track (IC or manager), cycle, and why plus more-of and less-of.
5. **Map freshness uses targeted, event-triggered refreshes,** not full reruns and not manual-only.
6. **The map carries packet readiness; drafting is a separate `packet` mode** near the deadline.
7. **Names:** `/flagrare:career` (the coordinator), `/flagrare:promotion`, `/flagrare:impact-scan` (renamed from senior-scan, with the old name kept as a trigger), and `/flagrare:opportunity-scan`.
8. **Build order:** promotion, then impact-scan, then opportunity-scan, then career.

## Architecture

| Skill | Job | Cadence | Writes |
|---|---|---|---|
| `promotion` | Target, company process, rubric gap, org, who knows your work, plan | First run, then targeted refreshes | `promotion-map.md`, `promotion-map.json` |
| `opportunity-scan` | Proposes 2-3 things the user could own end to end | About monthly | `initiatives.json` |
| `impact-scan` | Where to weigh in on others' threads | Daily or weekly | `scan-state.json`, `contributions.log.md`, staleness flags |
| `career` | Runs what's due; one combined digest; builds the board | On demand or scheduled | Board only |

Every skill reads the map. **Only `promotion` writes it** (single-writer shared contract). Scans signal staleness by writing flags, and the next `promotion` refresh acts on them.

### Shared state: `~/.claude/skills/flagrare/career/`

- `promotion-map.md`: the human document, the one the user brings to a 1:1.
- `promotion-map.json`: the same facts, machine-readable (schema below).
- `initiatives.json`: proposed, active and done initiatives. **At most one is active.**
- `contributions.log.md`: the append-only evidence log, moved from `senior-scan/`.
- `scan-state.json`: impact-scan dedupe, formerly `senior-scan/state.json`.
- `flags.json`: staleness flags from scans (`{section, reason, source, raised_at}`).
- `voice.md`: moved from `senior-scan/`.

All writes go through the Write tool. A sandboxed Bash cannot write under `~/.claude/skills`.

### Shared load-state step (every skill runs it first)

1. If `career/` is missing and `senior-scan/` exists, copy `state.json` (as `scan-state.json`), `contributions.log.md` and `voice.md` into `career/`. Leave `senior-scan/MOVED.md` pointing to the new folder. Never delete the originals.
2. Config: read `skills["impact-scan"]`, falling back to `skills["senior-scan"]`. Read the board directory from `skills.career.board.dir`, falling back to `skills["senior-scan"].board.dir`. Fallback-key migration: the old keys keep working, and new writes use the new keys.
3. Load the map and flags if present. Every consumer must handle "no map yet".

### `promotion-map.json` (schema sketch)

Every fact object carries `source` (a link or a quoted location), `checked_at` (ISO date), and `status`, one of `verified`, `unverified` or `inferred`. Conflicting sources are stored as a list of alternatives, never collapsed into one.

```json
{
  "target": { "current_level": "...", "target_level": "...", "track": "ic|manager",
              "cycle": "...", "why": "...", "more_of": ["..."], "less_of": ["..."],
              "level_is_terminal": {"value": true, "source": "...", "status": "verified"},
              "current_level_band": {"value": "2-5 years", "source": "...", "status": "verified"} },
  "process": { "steps": [...], "decision_makers": [...], "calibration_room": {"value": [...], "status": "inferred", "source": "..."},
               "packet_template": {...}, "decision_process": {"artifact": "Product Gate DACI", "usual_driver": "PM", "source": "..."} },
  "calendar": { "cycle_name": "...", "packet_deadline": {"value": "YYYY-MM-DD", "status": "inferred"},
                "calibration": {...}, "effective": {...},
                "manager_conversation": {"comfortable_by": "...", "absolute_by": "...", "status": "inferred"} },
  "rubric": { "artifact": {"name": "...", "source": "..."}, "prose_mismatches": [...],
              "rows": [ {"id": "scope.proactive-discovery", "current_text": "...", "target_text": "...",
                         "status": "done|partial|not_started", "evidence": [...] } ] },
  "org": { "chain": [...], "options": [...], "changes": [...] },
  "people": [ {"name": "...", "role": "...", "relation": "...", "seen_your_work": true,
               "evidence": [...], "confirmed_by_user": true} ],
  "precedent": { "tier": "announcements|deep", "caveat": "announcements are narratives, not audits", "cases": [...] },
  "packet_readiness": [ {"section": "Scope, Impact and Execution", "state": "strong|thin|empty", "evidence_rows": [...]} ],
  "manager_questions": [...],
  "sections": { "<name>": {"checked_at": "...", "sources": [...]} }
}
```

### Contributions log format

The format stays `- <date> | <link> | <what it changed> | behavior: <...>`. The `behavior:` value becomes **a rubric-row id from the map** (for example `scope.proactive-discovery`). Free text is still accepted, so old entries keep working. The board parser, brag-doc and impact-timeline all accept both.

## `promotion`

The first run is long, and the skill says so up front. It runs in four phases and **saves the partial map after each one.**

1. **Target, process and calendar.**
   - Ask the four target questions.
   - Always look up whether the target level is terminal, and the expected time band at the current level.
   - The "why" changes the plan. A terminal level plus "peace of mind" makes the target the finish line. "Money" or "scope" means planning past it.
   - Find the process, the calendar, the packet template and how decisions get made (the decision document and who drives it), across every connected source. The HR portal is read through the browser only with the user's consent.
2. **Rubric gap.**
   - Find the artifact managers rate against, not prose about it. When they disagree, prefer the artifact and record the mismatch.
   - Ask for any check-in workbook the manager uses.
   - Mark each row done, partial or not started, with evidence from the contributions log and the user's work.
3. **Org and who knows your work.**
   - Org chart, who sits above each landing option, and upcoming changes.
   - People are found from evidence (the user's own interactions only), then confirmed and extended by the user.
   - The calibration room is inferred from the process doc, with the source sentence.
   - Precedent: the default tier reads past promotion announcements, with the narrative caveat. An optional deep tier cross-checks in code, docs and tickets who originated the work. It is off by default.
4. **Plan.**
   - The manager-conversation threshold is computed mechanically: packet deadline, minus holiday dead time, minus about 2 weeks for peer quotes, minus about 2 weeks for drafting and feedback, minus gap-closing time. It is output as "comfortable by X, absolute by Y", marked inferred when the calendar is unpublished, and re-checked when HR publishes.
   - Packet readiness.
   - Questions for the manager.

Rules:
- Quotes are verbatim from raw sources.
- Conflicts are shown, not resolved silently.
- **"Nothing found" is a valid result.** Every step ends with findings and sources, or a concrete question added to `manager_questions`.
- **Refresh** re-checks only stale sections (older than 90 days) or flagged ones, then asks "anything changed?".
- **`packet` mode** drafts the packet in the company's format from the map plus brag-doc, for the user to edit.

## `impact-scan` (renamed senior-scan)

Everything in senior-scan v1.42.0, plus:

1. **Scoring uses the map.**
   - Stretch means which open rubric row the item closes.
   - Audience means whether the item reaches a person whose `seen_your_work` is false.
   - Without a map, v1.42.0 scoring applies unchanged.
2. **Staleness flags.** Reorgs, departures, manager changes, and cycle calendars published by HR get written to `flags.json`.
3. **Recurring-problem hand-off.** A problem seen twice becomes a candidate in `initiatives.json` instead of another reply draft.
4. **Log entries tag rubric rows** (see the log format above).
5. **Draft rules in the skill text:**
   - Every chat draft ends with the link to where it lives.
   - Evidence links go inside the draft.
   - Every claim is hedged, and the tone is casual.
   - No unverified claim goes into a draft.

## `opportunity-scan`

- **Inputs:**
  - recurring pain (repeat questions, repeat incidents, support toil),
  - silent degradation,
  - ownership gaps (a new integrator unsupported, a team with no frontend engineer, work orphaned by a reorg),
  - unanswered invitations,
  - leadership priorities (themes docs, OKRs, a new director's focus),
  - candidates handed off by impact-scan.
- **Ranking:**
  - the user's `more_of` and `less_of`,
  - which open rubric row it closes,
  - who cares, and whether they have `seen_your_work`,
  - whether the user has standing in the area,
  - **whether someone is already on it** (checked before proposing),
  - whether it can finish before the target cycle.
- **Proposals fit the local decision process** (`process.decision_process`). If a PM drives the decision document, the proposal feeds evidence into it and does not go around it.
- **Proposal shape:**
  - the problem, with evidence links,
  - a hypothesis ("we believe X will Y because Z") with a success metric defined before building,
  - rough impact,
  - who cares, and why now,
  - the smallest first step,
  - a short pitch for the manager.
  - Nothing built on an unchecked claim.
- **Guardrails:**
  - One active initiative at a time.
  - An initiative counts as the user's only after manager alignment.
  - Runs about every 30 days.

## `career` (coordinator)

A freshness-driven scheduler. It decides what to run from timestamps and flags:

| Condition | Runs |
|---|---|
| No map | `promotion` first run, **after asking**: "full setup now (long), or scan only with today's config?" |
| A map section older than 90 days, or flagged | `promotion` refresh of those sections |
| No active initiative, or last opportunity-scan more than 30 days ago | `opportunity-scan` |
| Always | `impact-scan` |

- **Interactive vs scheduled.** A run started by `/loop` or a schedule never asks questions and never posts. Interactive steps are listed in the digest as "pending, needs you".
- **Combined digest, capped:**
  1. initiative status and next step,
  2. 3-5 weigh-in items (same table rules as senior-scan),
  3. one map line (open rubric rows, people who haven't seen the work, the manager-conversation dates, the packet deadline),
  4. pending interactive items,
  5. the **balance warning**, which lives only here: "all answering, nothing owned", computed from contributions in the window versus initiative progress.
- Any failed write or build goes in the caveat line.

## Board

- The template and `build.py` move from `skills/senior-scan/board/` to `skills/career/board/`.
- `build.py` takes explicit paths for the map, initiatives and log. This fixes the hardcoded `senior-scan/contributions.log.md`.
- `data.json` additions:
  - an `initiative` item kind (rendered as a card at the top),
  - `rubric_rows` per item,
  - a promotion panel: ISO deadline dates, gap counts, people who haven't seen the work.
- The log parser accepts both the old free-text `behavior:` values and the new rubric-row ids.

## Changes outside the four skills

- `impact-timeline/SKILL.md:51` hardcodes `~/.claude/skills/flagrare/senior-scan/contributions.log.md`. It must read `career/contributions.log.md`, falling back to the old path. Re-check `brag-doc` for the same.
- **Rename mechanics:**
  - `skills/senior-scan/` becomes `skills/impact-scan/`, with "senior scan" kept as a trigger phrase in its description.
  - A stub `skills/senior-scan/SKILL.md` redirects to `/flagrare:impact-scan` for one release, and is marked deprecated in the CHANGELOG.
  - README's senior-scan paragraph gets rewritten for the family.
- **Release:** minor version bump per milestone (`scripts/bump-version.py`), narrative CHANGELOG, annotated tag, GitHub release.

## Milestones (each shippable alone)

1. **`promotion`, plus the shared load-state step and the `career/` folder.** Senior-scan keeps working untouched.
2. **`impact-scan` rename,** with map-aware scoring, flags, hand-off and rubric-tagged log, plus the stub, the impact-timeline and brag-doc path fixes, and the board move. Without a map it behaves exactly like v1.42.0.
3. **`opportunity-scan`.**
4. **`career`,** plus the board's promotion panel and initiative card.

## Out of scope

- The deep precedent tier stays off by default.
- **No publishing** of the map or board, as an Artifact or anywhere else. It is local only.
- No company-specific integrations. Surfaces come from connected MCPs, as senior-scan does today.

## Acceptance tests (observable behavior)

1. An existing senior-scan user runs any of the four skills and loses no log entries, dedupe state or voice rules. `senior-scan/` stays intact, with a `MOVED.md` pointer.
2. `impact-scan` with no map produces the same digest shape and scoring as senior-scan v1.42.0.
3. With a map, an item that closes an open rubric row outranks an otherwise equal item that doesn't.
4. `promotion` Phase 4, given last year's calendar and no published current one, prints "comfortable by X, absolute by Y" with both marked inferred.
5. A scheduled `career` run posts nothing, asks nothing, and lists the interactive steps as pending.
6. `build.py` renders a log mixing old free-text `behavior:` values and new rubric-row ids without dropping either.
7. When two sources disagree on one fact (for example a reporting line), the map shows both with their sources.
8. Interrupting the first `promotion` run after Phase 2 leaves a readable partial map covering Phases 1-2.
9. `impact-timeline` still reads the contributions log after migration.

## Named patterns

- **Single-writer shared contract:** the map is written only by `promotion` and read by everyone else.
- **Freshness-driven scheduler:** `career` decides from timestamps and flags, not fixed steps.
- **Append-only event log:** contributions are only ever appended.
- **Fallback-key migration:** new config keys, with old keys still read.

## Origin

Field-tested the hard way on 2026-09-30. A senior-scan session grew into a full day of manual promotion research:

- org charts from Miro and Notion,
- the promotion process from Confluence, SharePoint and Slack,
- the Senior rubric,
- the calibration timeline,
- who knows the user's work,
- a cross-check of nine promoted engineers in GitHub, Notion and Jira.

Each step is now a phase of `promotion`. Each correction the user made in that session is now a rule: sources over memory, conflicts shown, "under the hood" goals asked rather than assumed, and draft links always given.
