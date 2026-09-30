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

Work the user could own. Impact-scan records problem-type items through `career_state.py candidate`, once per scan run: a new evidence link adds a sighting (`seen_count` goes up), a link already recorded changes nothing, so the same thread continuing never counts twice. At `seen_count` 2 or more impact-scan hands the problem off instead of drafting. `/flagrare:opportunity-scan` ranks the candidates. At most one item is `active`.

```json
[{ "id": "stable-slug", "title": "plain words", "evidence": ["<link>"], "seen_count": 2,
   "first_seen": "2026-09-25", "last_seen": "2026-09-30", "status": "candidate|proposed|active|done|dropped" }]
```
