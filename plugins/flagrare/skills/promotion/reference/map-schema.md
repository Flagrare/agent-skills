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
    "rows": [{"id": "scope.proactive-discovery", "area": "Scope & Impact",
              "current_text": {}, "target_text": {},
              "status": "done|partial|not_started", "evidence": ["log line or link"]}]
  },
  "org": {"chain": [{}], "options": [{}], "changes": [{}]},
  "people": [{"name": "...", "role": {}, "relation": "...", "seen_your_work": true,
              "evidence": ["link"], "confirmed_by_user": true}],
  "precedent": {"tier": "announcements|deep", "caveat": "announcements are narratives, not audits", "cases": [{}]},
  "packet_readiness": [{"section": "...", "state": "strong|thin|empty", "evidence_rows": ["rubric row id"]}],
  "manager_questions": ["..."],
  "sections": {"target": {"checked_at": "YYYY-MM-DD", "sources": ["..."]}}
}
```

Rubric row ids are `<area>.<short-slug>`, lowercase with hyphens, and stay stable across refreshes. Impact-scan tags contributions with these ids.
