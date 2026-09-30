---
name: impact-scan
description: Scan the org's communication surfaces (chat like Slack or Teams, open PRs, RFC docs and design docs, ticket threads, whichever MCPs are connected) for high-leverage discussions the user should weigh in on, decisions still being formed, people stuck or circling, questions squarely inside the user's domains, cross-team changes touching systems they own or depend on. Built for engineers working toward promotion, it hunts opportunities to operate at the next level (influence beyond assigned work), ranks them by leverage and credibility, drafts replies in the user's own voice for approval, and logs posted contributions as promotion evidence that /flagrare:brag-doc can later consume. Use whenever the user says "impact scan", "senior scan", "promo scan", "what needs my attention", "where should I weigh in", "anything I should jump into", "scan slack", "scan PRs", "catch me up on what's happening", or any variant of "where can I have the most impact today", even when the skill isn't named. Also trigger when the user talks about wanting more visibility, more scope, or operating above their level.
---

# Impact Scan

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. Enforced by a repo hook. See `/flagrare:write-docs`.

Promotions lag behavior: you operate at the next level first, and the title follows. This skill hunts the openings where that operating can happen, decisions being shaped, people stuck, questions only this user can answer well, cross-team work touching their systems, and turns them into a ranked digest with ready-to-approve drafts.

The failure mode it must never enable is performative commenting. Shallow opinions dropped in ten visible threads read as noise, not seniority, and actively hurt a promotion case. The bar for surfacing an item: **would this user's contribution change the outcome, and do they have specific knowledge or context that gives them standing?** If either answer is no, the item dies, no matter how visible the thread is. Two substantive contributions beat ten drive-bys.

## Surfaces

The scan runs over **surfaces**: the places where decisions form and people get stuck. Three kinds, in rough order of how often they matter:

- **Chat** (Slack, Microsoft Teams, Discord, Google Chat): fast-moving threads, short decision windows.
- **Code review** (GitHub via MCP or `gh`, GitLab, Bitbucket): open PRs and their review threads.
- **Docs and tickets** (Confluence, Notion, Google Docs, Jira, Linear): often the highest-leverage surface of all. An RFC or design doc in its comment period is literally a decision being formed with an explicit window, exactly what the Timing axis rewards.

Which surfaces this user scans is decided at onboarding from the MCPs actually connected in the session, not hardcoded. Slack and GitHub are the reference implementations with detailed sweep instructions below; any other readable surface runs the generic sweep. At run time, skip any configured surface whose MCP is missing from the session and say so in the digest header; if no surface is reachable, stop and tell the user what to connect.

The scan is **read-only**. Sweep agents must never post, react, comment, or approve anything, and neither may the main flow without the explicit approval gate below.

## Setup and state (every run)

Config lives in the shared **`~/.claude/skills/flagrare/config.json`**: skill-agnostic keys (GitHub login, display name, repo scope) at the top level, impact-scan keys under `skills["impact-scan"]`. This skill was called senior-scan: when `skills["impact-scan"]` is missing, read `skills["senior-scan"]` instead, and write any changes back under `skills["impact-scan"]`. The first time you write that block, copy the whole senior-scan block into `skills["impact-scan"]` and then apply the change, so nothing is lost; leave the senior-scan block in place. Mutable files live in **`~/.claude/skills/flagrare/career/`** (`scan-state.json`, `contributions.log.md`, `voice.md`), shared with the other career skills and outside the plugin tree so they survive plugin updates. Their shapes are in `<plugin root>/lib/career/STATE.md`, where the plugin root is two directories above this skill's base directory. The user's **board** (a local HTML dashboard of open items and the evidence log, see workflow step 7) lives wherever `skills.career.board.dir` points, falling back to `skills["senior-scan"].board.dir`.

Write these files (and `config.json`) with the Write tool, never from Bash: a sandboxed Bash cannot write under `~/.claude/skills`, and a failed state write silently breaks dedupe across runs. Reading them from Bash is fine; expand `~` explicitly as `$HOME`.

**Load state first, every run.** Run `python3 <plugin root>/lib/career/career_state.py plan --home "$HOME"` and apply each `write` action with the Write tool, reading the target first if it exists (the Write tool will not overwrite a file it has not read). This brings over, or merges in, anything still in the old `senior-scan/` folder: the contributions log keeps every entry, the scan state keeps every seen item. A `mkdir` action needs no separate step. **Never delete anything.**

If `onboarding_complete` is not `true` in the impact-scan block (or the senior-scan block it falls back to), run onboarding. Reuse any top-level keys another flagrare skill already collected (ask only for what's missing), and only write the `skills["impact-scan"]` block (plus `skills.career.board`) and missing top-level keys; leave other skills' blocks untouched.

### Onboarding

The interview is half discovery, half confirmation: propose from real data wherever possible so the user is confirming lists, not composing them from memory.

1. **Identity.** GitHub login (detect via `gh api user --jq '.login'` or the GitHub MCP `get_me`, confirm) and repo scope (`org:<name>`, `user:<login>`, or explicit `owner/repo` list). Chat handle: look the user up with the chat MCP's user search, confirm the match.
2. **Career target.** Ask current level and target level, then which next-level behaviors to hunt for. Offer defaults by transition and let the user edit or paste their company ladder's actual language:
   - toward **senior**: influence beyond assigned tickets, unblocking others, owning technical decisions in their domain, raising the quality bar
   - toward **staff**: cross-team leverage, setting direction, connecting efforts that don't know about each other, derisking big decisions early
   The chosen behaviors become the definition of the Stretch axis (see Scoring), so they should be concrete. Once the user has a promotion map (`/flagrare:promotion`), its open rubric rows replace these behaviors for scoring; the config list stays as the fallback.
3. **Domains of real standing.** Spawn a discovery agent over the user's recent GitHub activity (authored PRs, reviews given, comment threads) to propose the areas where they demonstrably know things: systems, failure modes, conventions. Present the proposal; the user confirms, trims, adds. For each domain also collect 2-4 search keywords. Credibility scoring depends on this list being honest, so tell the user: list what you actually know, not what you want to know.
4. **Surfaces.** List the MCPs connected in the session that can read a surface (chat, code review, docs, tickets) and ask which should feed the scan, the same detect-and-opt-in move `/flagrare:standup-report` uses for `extra_mcps`. For each chosen surface, collect its scope by proposing from real data:
   - **chat**: channels, proposed via channel search using team names and domain keywords; include team channels, eng-wide channels, and incident/announcement channels
   - **code review**: repos, proposed from the user's recent activity within the repo scope
   - **docs**: spaces, databases, or folders where RFCs and design docs live, proposed via the doc MCP's search using the domain keywords
   - **tickets**: projects or teams whose comment threads matter, proposed the same way
5. **Audience (optional).** Names whose visibility matters for the promotion case: manager, senior/staff engineers, adjacent team leads. Powers the Audience score; without it that axis defaults to 1 and the skill says so.
6. **Voice.** Fetch a sample of the user's own recent writing (their Slack messages, their PR review comments, not other people's), distill 5-8 observed rules (sentence length, hedging style, formality, emoji use, how they disagree), and write them to `voice.md`. Show the rules for confirmation. If no sample is reachable, fall back to the generic drafting rules below and note it.
7. **Board.** Ask where the board should live (default `~/career-board`) and save it as `skills.career.board.dir`. If the user already keeps a dashboard of these items, point `skills.career.board.dir` at its folder instead of creating a second one. The board itself is created at the end of the first scan (workflow step 7).

Save, then show the full config summary for one final confirmation and set `onboarding_complete: true`.

```json
{
  "github_login": "aturing",
  "display_name": "Alan",
  "repo_scope": "org:acme-corp",
  "skills": {
    "impact-scan": {
      "onboarding_complete": true,
      "slack_handle": "@alan",
      "current_level": "mid",
      "target_level": "senior",
      "target_behaviors": ["influence beyond assigned tickets", "unblocking others", "owning decisions in the billing domain"],
      "domains": [
        { "name": "billing reconciliation", "keywords": ["reconcile", "ledger", "invoice drift"] }
      ],
      "surfaces": [
        { "type": "chat", "mcp": "slack", "scope": ["#eng-billing", "#eng-announcements", "#incidents"] },
        { "type": "code-review", "mcp": "github", "scope": ["acme-corp/billing-service", "acme-corp/payments-api"] },
        { "type": "docs", "mcp": "confluence", "scope": ["ENG space, RFC section"] }
      ],
      "audience": ["grace (manager)", "dknuth (staff)"],
      "exclusions": ["#random", "PRs the user authored"]
    },
    "career": {
      "board": { "dir": "~/career-board" }
    }
  }
}
```

Re-run any onboarding step when the user says "reconfigure", or when they say the scan keeps looking in the wrong places.

## Workflow

### 1. Load state and window

Run the load-state step from Setup first (`career_state.py plan`, applied with the Write tool), then read `career/scan-state.json` (`{ "last_run": iso8601, "seen": [{ "id", "source", "surfaced_at", "status" }] }`). The scan window is `last_run` to now; if no state exists, default to the last 48 hours, capped at 7 days. Items already in `seen` are only re-surfaced if they escalated: a new decision point, a new unanswered question, a thread reopened.

Then get the scoring inputs: run `python3 <plugin root>/lib/career/scoring.py context --home "$HOME"`. It prints `has_map`, the map's `open_rows` (rubric rows not yet done, each with `id`, `area` and `target_text`), `unseen_people` (people who have not seen the user's work yet), and a `fallback` with the configured `target_behaviors` and `audience`. The sweeps and step 3 use them.

### 2. Sweep in parallel

Spawn **one read-only sweep subagent per configured surface**, all in the same message so they run concurrently. Each gets its surface's scope, the domain map with keywords, the exclusions, the user's identity (so their own posts are skipped), and the time window.

Every sweep hunts the same four signals: (a) a decision still being formed (architecture, API contracts, migrations, process); (b) a question nobody has answered well, or a thread going in circles; (c) a discussion inside the user's domains that is missing context the user has; (d) work from other teams that touches systems the user owns or depends on. And every sweep returns the same shape, raw findings only, no ranking: location and link, participants, a 2-3 sentence summary, matched signal(s), and the specific gap the user could fill.

When `has_map` is true, each sweep also returns a separate short list of **map events**, exempt from the ignore rules below: a reorg or team change, someone leaving, a new manager or director, a change to the promotion process, or HR publishing the review calendar. Each event has its link and one plain sentence. These are not items to weigh in on; they feed the staleness flags in step 3b.

**Chat sweep (reference: Slack).** Read recent activity in each configured channel, follow interesting threads, and additionally run 2-3 keyword searches from the domain map, since relevant discussions happen outside configured channels. Ignore social chatter, resolved threads, FYI-only announcements, and threads where the right people are already converging.

**Code-review sweep (reference: GitHub).** List open PRs in the configured repos updated within the window and not authored by the user, then read the promising ones including review threads. Also hunt for: PRs whose changed paths touch the user's domains, and approaches carrying a risk the discussion hasn't caught, judged against the domain map's known failure modes. Ignore approved-and-converging PRs, trivial changes, and PRs where requested changes are simply in progress.

**Generic sweep (any other surface: docs, tickets, other chat platforms).** Enumerate items in scope updated within the window (pages, tickets, threads), read the ones with active human discussion, and apply the four signals. On docs surfaces, treat unresolved comment threads and open review periods on RFCs and design docs as prime candidates: they are decisions with explicit windows. Ignore items with no discussion, resolved threads, and pure status updates.

### 3. Score and cut

Score each candidate 0-2 on five axes:

- **Leverage**: would weighing in change the outcome, or just add a voice? A decided thread scores 0.
- **Credibility**: does the user have specific knowledge, context, or ownership the participants lack? Generic "good point" opinions score 0.
- **Stretch**: does this move one of the `open_rows` forward, beyond the user's assigned lane? Pick the row it moves from `open_rows` only, and never invent a row id. With no map or no open rows, use the configured target behaviors instead. Routine work in their own tickets scores low.
- **Audience**: who will see the contribution? 2 if someone in `unseen_people` will, 1 if only people who already know the user's work will, 0 if nobody whose view matters will. With no map, or when `unseen_people` is empty (the map has no people yet), use the configured audience as before: will they (or their equivalents) see it? With neither, it defaults to 1.
- **Timing**: is the window still open? A decision landing today scores 2; something simmering for weeks scores 1.

**Hard filter first:** drop anything with Leverage 0 or Credibility 0, regardless of the other axes. That is the anti-performative rule, and it is not negotiable, it protects the user's reputation. Then run step 3b (flags from the sweeps' map events, hand-off from the problem-type survivors), so problems ready for hand-off leave the ranking and flags are known before the digest. Rank what is left by total and keep at most 5. Dedupe against `scan-state.json` before presenting.

### 3b. Flags and hand-off (with a map, before the cut)

This step runs only when `has_map` is true; without a map, skip it and the digest has no Flags raised or Handed off lines. It keeps the other career skills current through two small records. Write each with the Write tool from the action the script prints, reading the target first if it exists. When several calls plan writes to the same file, apply them one at a time: write the first result, then run the next call, so each one sees the file as it now is.

**Staleness flags.** For each map event the sweeps returned (these never need to pass the hard filter), raise a flag for the map section it makes out of date: a reorg or team change (`org`), someone leaving or a new manager or director (`org` and `people`), a change to the promotion process (`process`), HR publishing the review calendar (`calendar`). Run `python3 <plugin root>/lib/career/career_state.py flag --home "$HOME" --section <section> --reason "<what changed, plain words>" --source <link> --today <YYYY-MM-DD>`. `--section` must be one of the map's sections listed in `<plugin root>/lib/career/STATE.md`; the script rejects anything else. The same flag is never raised twice.

**Hand-off of recurring problems.** Some items are problems rather than decisions: something broken, missing, or painful for users or partners (a class of failures, a gap nobody owns, the same question asked again). Record each problem-type item that passes the hard filter, once per scan run: `python3 <plugin root>/lib/career/career_state.py candidate --home "$HOME" --id <stable-slug> --title "<problem in plain words>" --evidence <link> --today <YYYY-MM-DD>`. To find an earlier sighting, compare with the existing candidates in `initiatives.json` by title and evidence; reuse that id when it is the same underlying problem, otherwise choose a new stable slug. A second sighting means the same problem showing up somewhere else (a different thread, incident or ticket), not the same thread continuing; the script ignores an evidence link it already has, so an escalating thread never counts twice.

Record every sighting from this run first, then decide hand-offs: two new threads about the same problem in one run count as two sightings, and neither gets a draft once the count reaches 2. Read the candidate's `seen_count` from the planned `initiatives.json` content, or, when the script plans nothing (the link was already recorded), from `initiatives.json` itself. At 2 or more the problem is handed off: it leaves the ranking before the top-5 cut (it never takes one of the 5 slots), gets no draft, appears only on the digest's **Handed off** line, and goes into `scan-state.json` with status `handed_off` in step 6. Owning the fix is worth more than a third comment. The candidates wait in `initiatives.json` for `/flagrare:opportunity-scan` (coming in a later release).

### 4. Present the digest

The digest is a to-do list, not a report. The user should know what to do from the table alone, and read an item's block only when they act on it. Write the table for a reader who has read none of these threads and remembers nothing from the scan: they may open it hours later, or see it re-listed mid-session after other work. A row that only makes sense to someone who just ran the sweeps has failed, however short it is.

Do not relay each sweep's findings as it lands; the digest is the only output. When a status line is forced (a sweep finishing, the harness asking for an update), give one line naming the sweeps still running, with no findings.

```
## Impact scan: <date>, <window>. <one line of caveats: surfaces skipped, state not saved>

| # | What's going on | What you'd do | Why it matters | Next step |
|---|---|---|---|---|
| 1 | <whose thing, what it is in product terms, where it stands; the thing's name is the link> | <verb-first move, plain words> | <impact, max 12 words> · <target behavior> | Send draft |
| 2 | A restaurant got no email or text for two app orders on 9/24; a support lead asked in the [squad channel](<permalink>) whether it should have, nobody answered | Tell them which email should have fired and whether it did | A partner missed real orders, support is stuck · unblocking others | Check first: look the order up in the email tool |

### 1. <same verb-first action>
<one sentence: what is happening and where it stands>. <one sentence: why you, naming the fact or context only you bring>. (<rubric row id>, only with a map)
> <draft, at most 3 sentences>

(repeat per item)

**Cut:** <near-miss, reason>; <near-miss, reason>; ...
**Flags raised:** <map section>: <what changed> (only when step 3b raised a flag)
**Handed off:** <problem in plain words> (seen <N> times, recorded in `initiatives.json`) (only when step 3b handed one off)
```

Rules that keep it scannable:

- **"What's going on" gives the context before the ask.** One plain sentence, 25 words at most: whose thing it is, what it is in product terms, and where it stands (unreviewed, approved, question unanswered since Tuesday). "a teammate's [peak-times PR](url) promises a fallback message when loading fails; two people approved it", not "the peak-times fallback PR". The thing's name carries the link, so there is no separate Where column.
- **The table speaks product, not code.** No PR numbers, ticket keys, channel ids, function names, or flags in any table cell: a reader cannot decode "a missing error flag on a PR number" without the context they don't have. Say what breaks for whom ("a server error shows the full-page error screen instead of the retry button"). Code identifiers and `file:line` belong in the item block and the draft, where the reader is already acting.
- **Actions start with a verb and name the move in plain words**: "Point out that a server error blanks the page instead of showing the retry", not "Flag a missing error flag on a PR number", and not "Item report error handling".
- **Re-listing follows the same rules.** When remaining items are shown again later in the session, rebuild each row from scratch for a cold reader; never shorten a row to "the same gap" or "item 1's issue" because it was discussed earlier.
- **"Why it matters" says what changes if the user acts, then the behavior it exercises.** The impact is 12 words at most, the concrete outcome ("stops a 502 blanking a page before launch", "a modifiers decision is being made without the person who designed them"), never the score or a restatement of the action. After a `·`, name what it exercises in two or three plain words: with a map, what the open row asks for, taken from its `target_text` ("finding problems" for a row about proactively discovering problems); otherwise the configured target behavior ("quality bar", "unblocking others"). Row ids are code-like, so they go in the item block, never in the table. Rows are ordered by score, so this column is what explains the ranking.
- **Every item ends in a next step.** Either a draft ready to send, or `Check first:` with the single concrete check (a query, a code path to trace) that would make a draft safe. Never a draft built on a claim that has not been verified.
- **No field labels in item blocks** ("What's happening:", "Why you:", "Suggested angle:"). The two sentences and the draft carry all of it.
- **Evidence goes inside the draft, not before it.** If the draft already cites `file:line`, the block does not repeat it.
- **Near misses fit on one line.** A short reason each, so the filter stays honest and tunable without adding a section.
- **Stop after the cut line** (and the flags and hand-off lines when present). No closing summary. Ask only which items to act on.

### 5. Drafting rules

Read `voice.md` first if it exists; its observed rules win over the generic ones. Generic floor, applied always:

1. **Short and direct.** Three sentences at most, no preamble, no "Great discussion!", no wrap-up flourish.
2. **No LLM tells.** No em-dashes, no "aligns with", no rule-of-three constructions, no self-congratulation.
3. **First person, explicit.** "I ran into this", never "Ran into this".
4. **Hedge pushback collaboratively, without interrogating.** State the concern plainly with its evidence and admit possible missing context. A closing question is for genuine uncertainty, when you actually need the author's context to resolve the point, not a mandatory sign-off: ending every draft with "does that match your understanding?" reads as a tic, and a faux-question that is really an assertion ("am I reading this right that this is unused?") reads passive-aggressive, which is worse than asserting. When the evidence is on the table and you are confident, say the thing and stop.
5. **Contextualize references.** Never a bare ticket number; say what the ticket is with the key in parentheses.
6. **Cite PRs and commits, not people.** Explaining where a behavior came from means pointing at the PR or SHA, never naming who broke it.
7. **Substance first.** Every draft must contain the specific fact, risk, or suggestion that justified surfacing the item. If someone without the user's context could have written the draft, the item fails the credibility bar: cut it instead of shipping filler.

**Never post anything anywhere.** Every draft waits for the user's explicit approval of that specific message. Posting without it is the one unforgivable failure of this skill.

### 6. Update state and the evidence trail

After presenting, write `career/scan-state.json` with the Write tool: update `last_run`, append surfaced items with `status: "surfaced"` and any item handed off in step 3b with `status: "handed_off"`. If the write fails, say so in the digest's caveat line, since the next run will re-surface the same items. Then update the board (step 7) in the same turn.

When the user approves and posts a contribution (or says they handled it), set that item's status to `"contributed"` and append to `career/contributions.log.md`:

```
- <date> | <link> | <one sentence: what the contribution was and what it changed> | behavior: <target behavior exercised> | row: <rubric row id>
```

Add the `| row: <id>` field only when there is a map and the item moved one of its `open_rows`; otherwise end the line after `behavior:`. With a map, `behavior:` still names the closest configured target behavior, because the board's coverage panel counts those; the row id goes in `row:`. The format is in `<plugin root>/lib/career/STATE.md`.

This log is the promotion evidence trail, the lagging indicator made legible. When the user later runs `/flagrare:brag-doc` or builds a promo packet, point them at it; brag-doc should treat it as a first-class source.

Every log entry is also a board update: rebuild so the evidence log shows it, and move the item to `waiting` (a reply is expected) or `done`.

### 7. Keep the board current

The board is the expected output of every scan, not an extra: a local page the user opens to see what to act on next, what is waiting on someone else, and the evidence log. The digest is read once; the board is what they come back to. It is display-only: `data.json` is the single source of truth, the user tells you in chat what changed, and you update the file and rebuild.

**First scan, or no board yet.** If no board directory is configured under either `skills.career.board.dir` or `skills["senior-scan"].board.dir` (including users onboarded before the board existed) or the folder has no `data.json`, create it at the end of this run: ask for the location once (default `~/career-board`), save it as `skills.career.board.dir`, write `data.json` from this scan, build, and tell the user how to open it. Never finish a scan with no board and no caveat saying why.

**Every update.** Write `<board dir>/data.json` with the Write tool, then run `python3 <plugin root>/lib/career/board/build.py <board dir>`, which renders `board.html` from the bundled template plus the contributions log (it reads the career log and any entries still only in the old senior-scan log). If the sandbox blocks the write outside the working folder, rerun the build outside the sandbox. Rebuild after the scan AND whenever an item changes (a draft posted, an item now waiting on someone, done, dropped), in the same turn you update `scan-state.json` or the log, so the board never lags the conversation. If the build fails, say so in the caveat line.

`data.json` shape:

```json
{
  "scan": { "date": "2026-09-30", "window": "Sep 29 14:18 UTC to Sep 30 13:30 UTC", "caveats": "Jira skipped" },
  "behaviors": ["raising the quality bar", "unblocking others"],
  "items": [{
    "id": "short-stable-slug", "rank": 1, "status": "todo",
    "urgency": "today", "effort": "15 min", "deadline": "2 approvals, could merge today",
    "source": "github", "kind": "review",
    "action": "Point out the flyout always shows the last 7 days",
    "link": "https://...", "context": "Whose thing, what it is, where it stands",
    "why": "Impact in 12 words or less", "behavior": "raising the quality bar", "rubric_rows": ["scope.proactive-discovery"],
    "draft": "ready-to-send text", "draft_where": "GitHub inline comment on file.js:60",
    "check_first": "the one check that makes a draft safe",
    "waiting_on": "a reviewer", "since": "2026-09-29"
  }]
}
```

- `status`: `todo` (shown in the ranked list), `waiting` (raised, waiting on someone; set `waiting_on` and `since`, and after 3 days the board suggests a nudge), `done`, `dropped`.
- `urgency`: `today` (could merge or close before the user acts), `week`, `later`. `deadline` says why.
- `behaviors`: the configured target behaviors; the board shows evidence coverage for each.
- `rubric_rows`: optional; the ids of the map rows the item moves (from `open_rows`), empty or absent without a map.
- An item carries either `draft` or `check_first`, never a draft built on an unverified claim. The same product-language rules as the digest table apply to `action`, `context` and `why`.
- Keep ids stable across runs. Before adding an item, check for an existing one about the same thread: update it instead of adding a duplicate, and if the new scan contradicts its text, fix the text or flag the conflict to the user.
