# Career state files

Shared by `/flagrare:promotion`, `/flagrare:impact-scan`, `/flagrare:opportunity-scan` and `/flagrare:career`, which runs whichever of the others are due. They live in `~/.claude/skills/flagrare/career/`, outside the plugin tree so they survive updates. Skills write them with the Write tool (a sandboxed shell cannot write there); the scripts in this folder only read and plan. `career_state.py plan` brings over and merges anything still in the old `~/.claude/skills/flagrare/senior-scan/` folder and never deletes it.

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
  "seen": [{ "id": "slack:C123:1790703452.608029", "source": "slack", "surfaced_at": "2026-09-30T13:30:00Z", "status": "surfaced|contributed|dropped|handed_off" }] }
```

When both the old and new files exist, the merge keeps the later `last_run` and the union of `seen` by `id` (the later `surfaced_at` wins, the career copy wins a tie, and a `contributed` item always wins over any other status for the same id). Items without an `id` are kept too. Other top-level keys are kept. For any other top-level key present in both files, the career value wins. A file that is not valid state is left alone rather than merged.

## voice.md

The user's observed writing rules, used for drafts. The newer of the old and new copies wins.

## promotion-map.json and promotion-map.md

Written only by `/flagrare:promotion`. Shape: `skills/promotion/reference/map-schema.md`.

## flags.json

Signals that part of the promotion map may be stale. Other skills append through `career_state.py flag`, which skips a flag when one for the same section already has the same reason or the same source; `/flagrare:promotion` reads them on refresh and removes the ones it handled.

```json
[{ "section": "org", "reason": "a new team lead was announced", "source": "<link>", "raised_at": "2026-09-30" }]
```

`section` is one of the promotion map's sections (`target`, `process`, `calendar`, `rubric`, `org`, `people`, `precedent`, `packet_readiness`, `manager_questions`).

## initiatives.json

Work the user could own. Two skills record candidates through `career_state.py candidate`: opportunity-scan, when the career coordinator runs it, keeps each proposal the user has not decided on as a candidate with one sighting (reusing an existing id); and, when the user has a promotion map, impact-scan records problem-type items (a recurring problem the user could fix, as opposed to a thread to answer) through `career_state.py candidate`, once per scan run: a new evidence link adds a sighting (`seen_count` goes up) and keeps the item's `status`, a link already recorded changes nothing, so the same thread continuing never counts twice. The hand-off threshold is impact-scan's rule, not the script's: at `seen_count` 2 or more it stops drafting replies for that problem and marks the scan item `handed_off` in `scan-state.json`. `/flagrare:opportunity-scan` checks each candidate for an existing owner, ranks it with its own findings, and records what the user keeps through `initiatives.py`:

- `propose` moves a candidate (or a new problem, which needs at least one evidence link) to `proposed` and adds a `proposal` object; `problem`, `hypothesis`, `metric`, `first_step`, `pitch` and `owner_check` are required, the other fields optional. It refuses an item that is already `active` or `done`. It keeps `seen_count`, `first_seen` and every evidence link, and `career_state.py candidate` keeps the proposal when the problem is seen again.
- A candidate an opportunity scan drafted but the user has not decided on carries the drafted fields as `draft_proposal` (from `career_state.py candidate --details`). It is not a sighting, it never replaces a kept `proposal`, and `propose` removes it.
- `status` makes one move at a time: `candidate` or `proposed` to `dropped`, `proposed` to `active`, `active` to `done` or `dropped`, `dropped` back to `candidate`, and `dropped` to `dropped` again (a dismissed problem that came back and was dismissed again, which restamps `dropped_at`). Each move stamps `<status>_at`, and a note passed with it is kept as `<status>_note` (for `active`, inside `aligned`).
- **At most one item is `active`, and only after manager alignment:** the script refuses a second one (naming the first) and refuses `active` without `aligned-with`, which it records as `aligned`.
- A `dropped` item is proposed again only when it was seen after `dropped_at`.

```json
[{ "id": "stable-slug", "title": "plain words", "evidence": ["<link>"], "seen_count": 2,
   "first_seen": "2026-09-25", "last_seen": "2026-09-30", "status": "candidate|proposed|active|done|dropped",
   "proposal": { "problem": "...", "hypothesis": "We believe X will Y because Z", "metric": "...", "impact": "...",
                 "who_cares": "...", "why_now": "...", "first_step": "...", "pitch": "...", "owner_check": "what was searched",
                 "decision_fit": "...", "rubric_rows": ["scope.proactive-discovery"] },
   "proposed_at": "2026-10-01", "aligned": { "with": "...", "on": "2026-10-03", "note": "..." }, "active_at": "2026-10-03",
   "dropped_at": "...", "dropped_note": "..." }]
```

## opportunity-state.json

When opportunity-scan last ran, so it and `/flagrare:career` can tell when the next one is due (every `skills["opportunity-scan"].cadence_days`, default 30):

```json
{ "last_run": "2026-10-01" }
```
