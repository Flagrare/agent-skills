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

- `propose` moves a candidate (or a new problem, which needs at least one evidence link) to `proposed` and adds a `proposal` object; `problem`, `hypothesis`, `metric`, `first_step`, `pitch`, `owner_check` and `lever` (what in the user's seat moves the metric) are required; `baseline`, `target` and `by` are expected, the other fields optional. It refuses an item that is already `active` or `done`. It keeps `seen_count`, `first_seen` and every evidence link, and `career_state.py candidate` keeps the proposal when the problem is seen again.
- A candidate an opportunity scan drafted but the user has not decided on carries the drafted fields as `draft_proposal` (from `career_state.py candidate --details`). It is not a sighting, it never replaces a kept `proposal`, and `propose` removes it.
- **Ranking.** A `proposal` or `draft_proposal` can carry `score`: one entry per factor (`impact`, `lever`, `fit`, `rubric`, `who_notices`, `standing`, `evidence`, `timing`), each `{"value": 0|1|2, "why": "<one line>"}`. The scripts refuse an unknown factor or a value outside 0 to 2. `initiatives.py context` ranks `proposed` and `candidates` by the weighted total (impact counts double, so the most is 18; `skills["opportunity-scan"].weights` can set any factor to 1, 2 or 3) and adds `rank` `{total, max, is_fix}` to each; `is_fix` means impact scored 0, so the board lists it under "Fixes, not projects". Unscored items come last, most seen first.
- `status` makes one move at a time: `candidate` or `proposed` to `dropped`, `proposed` to `active`, `active` to `done` or `dropped`, `dropped` back to `candidate`, and `dropped` to `dropped` again (a dismissed problem that came back and was dismissed again, which restamps `dropped_at`). Each move stamps `<status>_at`, and a note passed with it is kept as `<status>_note` (for `active`, inside `aligned`).
- **At most one item is `active`, and only after manager alignment:** the script refuses a second one (naming the first) and refuses `active` without `aligned-with`, which it records as `aligned`.
- A `dropped` item is proposed again only when it was seen after `dropped_at`.

```json
[{ "id": "stable-slug", "title": "plain words", "evidence": ["<link>"], "seen_count": 2,
   "first_seen": "2026-09-25", "last_seen": "2026-09-30", "status": "candidate|proposed|active|done|dropped",
   "proposal": { "problem": "...", "hypothesis": "We believe X will Y because Z", "metric": "...", "impact": "...",
                 "who_cares": "...", "why_now": "...", "first_step": "...", "pitch": "...", "owner_check": "what was searched",
                 "decision_fit": "...", "rubric_rows": ["scope.proactive-discovery"],
                 "score": { "impact": { "value": 2, "why": "..." }, "lever": { "value": 1, "why": "..." } } },
   "proposed_at": "2026-10-01", "aligned": { "with": "...", "on": "2026-10-03", "note": "..." }, "active_at": "2026-10-03",
   "dropped_at": "...", "dropped_note": "..." }]
```

## recognition.json

A cache of peer recognition from the company's recognition tool (Bonusly), written from `recognition.py fetch` and read by the board, promotion, brag-doc and impact-timeline without the network. The token is never stored here: it lives in `~/.config/flagrare/bonusly-token` (or `skills.career.recognition.token_file`).

```json
{ "fetched_on": "2026-10-01", "provider": "bonusly", "since": "2025-10-01", "until": "2026-10-01",
  "user": { "name": "...", "email": "...", "manager_email": "..." },
  "received": [{ "id": "...", "date": "2026-10-01", "giver": { "name": "...", "email": "..." }, "receivers": ["..."],
                "value": "team-first", "reason": "raw text", "text": "the thanks, cleaned",
                "plus_ones": ["..."], "plus_one_count": 0, "link": "https://bonus.ly/bonuses/<id>" }],
  "given": [ ...same shape... ] }
```

The `link` opens the bonus when the user is signed in to the tool.

## opportunity-state.json

When opportunity-scan last ran, so it and `/flagrare:career` can tell when the next one is due (every `skills["opportunity-scan"].cadence_days`, default 30):

```json
{ "last_run": "2026-10-01" }
```

## measurements.json

Impact measurements, written by `/flagrare:measure-impact` through `measurements.py` (plan-only, like the other scripts). One entry per piece of work measured or skipped:

```json
[{ "id": "stable-slug",
   "work": { "title": "plain words", "link": "<ticket, TDD, PR or log entry>", "kind": "ticket|tdd|project|log_entry" },
   "stage": "before|after|past|skipped", "skipped_reason": "",
   "impact_types": ["partners", "business"],
   "metric": { "name": "...", "why": "...", "priority_theme": "<theme from the map, when any>" },
   "source": { "category": "data warehouse", "tool": "...", "query": "<exact text, no credentials>", "run_at": "2026-10-02" },
   "baseline": { "value": "...", "as_of": "2026-10-02", "confidence": "direct" },
   "comparable": { "what": "...", "base": "per 10,000 bookings", "value": "...", "confidence": "supported" },
   "bet": { "sentence": "We believe ...", "range": "...", "confidence": "inferred" },
   "ownership": "mine|team|contributed",
   "launch_date": null,
   "checks": [{ "due": "2026-10-19", "after_days": 14, "done_at": null, "value": null, "verdict": "worked|didnt_work|cant_tell" }],
   "result": { "sentence": "", "confidence": "" },
   "created_at": "2026-10-02", "updated_at": "2026-10-02" }]
```

- Confidence levels: `direct`, `supported`, `inferred`, `speculative`, `unknown`. The script refuses anything else, an unknown stage, kind or ownership, dates not written `YYYY-MM-DD`, and a query that looks like it holds a credential.
- `plan` adds an entry or updates the one with the same id. It never changes `checks`, `launch_date` or `created_at`, even when the entry sends them: `launch` sets the launch date and creates checks 14 and 42 days later (`after_days`), and re-launching keeps each check already done and moves only the undone ones. `check` records a check and moves the entry to `after`. `skip` records a skip with its reason.
- `due` lists undone checks whose date has passed, `before` entries with no launch date 30 days after they were saved, and contributions-log entries whose link matches no measurement, counted from the later of 30 days ago and the first saved measurement, and not at all before the first one, so an existing log is never reported all at once (`--all-wins` counts every entry). Skipped entries never appear.
- `plan` never moves an entry back from `after` to `before`.
- A corrupt file is never overwritten: every command refuses until it is fixed.
