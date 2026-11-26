# promotion-map.json

Written only by `/flagrare:promotion`. Read by impact-scan, opportunity-scan and career. Check it with `python3 <plugin root>/lib/career/map_schema.py check <path>`.

## Facts

A fact is any object with a `value` or `alternatives` key, and every fact needs a `status`:

- Single source: `{"value": ..., "source": "<link or quoted location>", "checked_at": "YYYY-MM-DD", "status": "verified|unverified|inferred"}`
- Sources disagree: `{"status": "unverified", "alternatives": [fact, fact, ...]}`. Keep every alternative, and show all of them to the user.

Statuses:
- `verified`: read in the raw source, quoted verbatim.
- `unverified`: seen only in a summary, a search snippet, or secondhand.
- `inferred`: derived by reasoning (for example, who sits in calibration, or deadlines from last year's calendar).

Objects with a `status` but no `value` or `alternatives` (for example rubric rows, whose status is done, partial or not_started) are not facts.

## Sections

Absent sections mean "not researched yet", not an error.

```json
{
  "target": {
    "current_level": {}, "target_level": {}, "track": {}, "cycle": {},
    "why": "user's words", "more_of": ["..."], "less_of": ["..."],
    "level_is_terminal": {}, "current_level_band": {}
  },
  "process": {
    "steps": [{}], "who_initiates": {}, "decision_makers": {}, "calibration_room": {},
    "bar": {"value": {"months": 6, "text": "the rule, quoted"}, "source": "...", "checked_at": "...", "status": "verified"},
    "packet_template": {"sections": ["..."], "length": {}, "peer_feedback": {}},
    "decision_process": {"artifact": {}, "usual_driver": {}}
  },
  "calendar": {
    "cycle_name": "...", "packet_deadline": {}, "calibration": {}, "effective": {},
    "dead_windows": [["YYYY-MM-DD", "YYYY-MM-DD"]],
    "manager_conversation": {"comfortable_by": "...", "absolute_by": "...", "status": "inferred", "state": "ok|tight|past"}
  },
  "rubric": {
    "artifact": {}, "prose_mismatches": [{}],
    "rows": [{"id": "scope.proactive-discovery", "area": "Scope & Impact", "label": "Finding problems",
              "current_text": {}, "target_text": {},
              "status": "done|partial|not_started", "evidence": ["log line or link"],
              "next_step": "the single cheapest action that would add evidence this week",
              "assessment": {"target": "meets|not_yet", "current": "exceeds|meets|below", "since": "YYYY-MM-DD",
                             "reason": "one plain sentence", "proof": ["link"], "checked_at": "YYYY-MM-DD"}}]
  },
  "org": {"chain": [{}], "options": [{}], "changes": [{}]},
  "people": [{"name": "...", "role": {}, "relation": "...", "seen_your_work": true,
              "evidence": ["link"], "confirmed_by_user": true}],
  "precedent": {"tier": "announcements|deep", "caveat": "announcements are narratives, not audits", "cases": [{}]},
  "packet_readiness": [{"section": "...", "state": "strong|thin|empty", "evidence_rows": ["rubric row id"]}],
  "manager_questions": ["..."],
  "priorities": [{"theme": "Partner trust", "metric": {}, "baseline": {}, "target": {},
                  "owner_team": "Partners", "user_lever": "owner|input|none"}],
  "sections": {"target": {"checked_at": "YYYY-MM-DD", "sources": ["..."]}}
}
```

Rubric row ids are `<area>.<short-slug>`, lowercase with hyphens, and stay stable across refreshes. Impact-scan tags contributions with these ids. `label` is the plain name people read (on the board and in digests); `next_step` is set for rows that are not `done` and feeds the board's "biggest gaps" list. `priorities` is optional (older maps have none); it is written in Phase 1 with the process and calendar, and its facts are checked like the others. `packet_readiness` entries may carry a one-line `note`, which the board shows under the section's state.

A row's `assessment` is the skill's rating of that behavior, not a fact (it has no `value`), and a row without one is simply not rated yet. `map_schema.py check` reports an unknown `target` or `current`, a missing or bad `checked_at`, a `meets` with no `since`, and a `since` after `checked_at`. `process.bar` and `calendar.effective` together give the date a behavior must be met by to count this cycle (`effective` minus `months`); `coordinator.py assessment` reports which met rows hold that long.
