# Impact Timeline: Per-Source Playbook

Concrete recipes proven in a real full-tenure run (a 12-month window, 154 PRs, 8 sources). Adapt identifiers; keep the shapes.

## GitHub (gh CLI)

Bulk enumeration, paginated, bucketed later with awk:

```bash
# authored
for p in 1 2; do gh api "search/issues?q=org:{ORG}+is:pr+author:{LOGIN}&sort=created&order=asc&per_page=100&page=$p" \
  --jq '.items[] | [.created_at, (.pull_request.merged_at // "unmerged"), (.repository_url|split("/")|last), .number, .state, .title] | @tsv'; done > authored_prs.tsv
# reviewed (exclude own)
... q=org:{ORG}+is:pr+reviewed-by:{LOGIN}+-author:{LOGIN} ... > reviewed_prs.tsv
# monthly shape
cut -c1-7 authored_prs.tsv | sort | uniq -c
```

- Bucket twice: by created date (column 1) AND by merged date (column 2); "merged this month, created earlier" is a real per-month view and the created-date buckets alone miss it (`awk -F'\t' '$2 ~ /^YYYY-MM/ && $1 !~ /^YYYY-MM/'`).
- For a month-scoped reviewed-PRs pull, add `updated:YYYY-MM-01..YYYY-MM-31` to the `reviewed-by:` query. It approximates review activity (updated ≠ reviewed); for tenure-wide runs pull once unscoped and bucket by PR created date, accepting the same approximation.
- In Refs footnotes always prefix PR numbers with the repo (`server#6912` vs `summer#6912`); cross-repo number collisions are common in multi-repo orgs.
- Earliest PR validates the start date. Search covers archived org repos too, but also `git log --author={WORK_EMAIL}` in local clones of deprecated repos (filter by work email; same-first-name strangers exist in old history).
- PR titles usually embed ticket IDs; that plus tracker data often makes fetching PR bodies unnecessary.

## Tracker (Shortcut shown; same shape for Linear/Jira)

Per month: `stories-search owner=me completed=YYYY-MM-01..YYYY-MM-31`. The response's relatedEntities block is half the value: epic names/states, iterations, objectives, priority/severity labels, requester names. Track which epics reached done. For refresh runs, query only the gap window.

## Slack

One per-month search of the person's own messages:

```
from:<@USERID> after:YYYY-MM-01 before:YYYY-MM-01(next)
```

sort=score surfaces substantive messages over noise; concise format + no context keeps it cheap. Pass `channel_types=public_channel,private_channel` to exclude DMs: unscoped results skew heavily to DM chatter while nearly all substance (standups, bug-bash writeups, debugging threads, escalations) lives in channels. Gold: async standup updates (ready-made narratives), #eng-team debugging threads, incident escalations, architecture takes, security flags. Follow up with one targeted keyword search when a thread hints at an incident or initiative. DM-heavy early months mean onboarding; note and move on.

## Meeting notes (Granola)

`list_meetings` per month to spot high-signal titles (postmortems, demos, 1:1s, retros); read those directly with `get_meetings`. Then bulk natural-language queries over the whole window (these two recovered praise, assignments, an outage postmortem, and every all-hands number in the real run):

- "Across all meetings, what did {NAME} personally own, present, demo, decide, or get praised or credited for? Include dates."
- "Between {START} and {END}, what did {NAME} contribute, propose, or receive feedback about in 1:1s, retros, reliability checkpoints, and pod meetings?"
- "What product metrics and business numbers were mentioned in meetings: user counts, dollar volumes, OKR grades, adoption rates? Include dates and exact figures."
- "Was there a layoff, reorg, leadership change, or major contract win/loss discussed in any meeting during {WINDOW}? What was said about {NAME}'s own departure, and in what sequence relative to those events?"

Re-run the org-context query on the final refresh before delivery; these events cluster in the last weeks of a tenure and an early sweep misses them (in the real run, a sweep missed a layoff announced two days later). Cross-signal: tracker user records flipping to disabled between pulls means departures happened.

Long queries may background; keep working and fold in the notification result. Coverage rarely reaches the first weeks of tenure; say so rather than padding.

## BI / data platform (Mode + Snowflake recipe)

1. Locate: search Notion for "Data Wiki" / tool names. The wiki page typically links the platform URL and the access contact.
2. Access: open the platform in the automation browser; workspace Google SSO with the user's existing session frequently just works. If it doesn't, report the documented access contact instead of hacking around it.
3. Extract numbers via the platform's API from the authenticated page (rendered embeds are unreliable). Mode specifically:
   - Trigger a report run in the UI, note report token + run token from the URL.
   - `fetch('/api/{ws}/reports/{report}/runs/{run}')` until state=succeeded (often seconds even when the embed spins).
   - `fetch('/api/{ws}/reports/{report}/runs/{run}/query_runs')` lists named queries; each query's rows at `.../query_runs/{qr}/results/content.json`.
   - Aggregate in-page with JS (totals, tenure-window slices, distinct counts) and return only the summary object; raw row dumps blow the context for nothing.
4. Best derived claims: metric-at-start vs metric-now over the tenure window ("enrolled users grew from N to M, +X%"), tenure share of all-time volume, success-rate from status breakdowns.

## Datadog / Sentry

- RUM: discover application names first (aggregate by @application.name), then percentiles of @view.loading_time (nanoseconds) for after vs before windows. Retention (~30d) usually eats the "before"; pair current numbers with baselines recorded in meeting notes/checkpoints and cite both. Flag clamped windows: the tool warns, the document must too.
- Sentry: search_issues by error message for lifetime event/user counts of errors the person fixed; "zero recurrences since the fix" is a clean claim. 90d activity windows miss long-dead issues; drop rather than guess.
- Historical logs/events for old incidents are usually expired; the postmortem or Slack thread is the citation then.

## Writing patterns

- Month section: story-of-the-month paragraph, "What I shipped" (outcome-first, refs inline), judgment/unblocking blocks, "(from meeting records)" provenance tags, "**Measured by:**" block, compact Refs footnote.
- Summary: Product/Technical/Business metric groups with source+as-of-date, scale stats, tenure arc, five X-Y-Z interview stories.
- Voice: `/flagrare:brag-doc` rules (own it, quantify, no enumeration). House style: no em dashes, no emojis, no ticket IDs without inline descriptors.
- Deliverable: export folder with the markdown + the PR TSVs; memory pointer updated at the end.
