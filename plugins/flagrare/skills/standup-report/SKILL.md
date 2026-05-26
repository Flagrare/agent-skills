---
name: standup-report
description: Generate a narrative standup report covering everything code-related you shipped, reviewed, or addressed during your last working day — PRs merged, reviews left and answered, comments addressed, deploys that fired, tickets closed. Pulls from GitHub, local git across all your repos, release automation, and any installed tracker/Slack MCPs. The output is a short narrative paragraph plus a journal-style recap plus a slack-pasteable bullet list, written in human terms (the *thing* you fixed, not "PR #481"). Use whenever the user says "standup", "standup report", "what did I do yesterday", "yesterday recap", "daily recap", "what did I ship", "morning standup", "give me my standup", "summarize yesterday's work", or any variation. Also trigger right before a known standup time when the user opens a session.
---

# Standup Report

Generate a daily standup recap that reads like a human wrote it. The reader is either the user (preparing what to say at standup) or their team (skimming a Slack post). Either way, they want the *story* of yesterday's code work, not a JSON dump of commits.

The single rule that shapes everything below: **work is named by what it was, not by its ID.** "Fixed the image cache eviction" beats "Merged PR #481" every time. Nobody remembers numbers; everyone remembers the bug.

## Setup (first run only)

Check `{skill_directory}/config.json`. If missing, run setup.

### First-time setup

Use `AskUserQuestion` to collect:

1. **GitHub login** — needed for `author:`, `commenter:`, `reviewed-by:` searches. If missing, run `gh api user --jq '.login'` and confirm.
2. **Display name** — how to refer to the user in the narrative ("Alan reviewed two PRs" vs "you reviewed two PRs"). Default to first-person ("I").
3. **Repo scope** — one of:
   - `org:<name>` — all repos in a GitHub org (best for company work)
   - `user:<login>` — all repos under the user's account (best for personal projects)
   - explicit list of `owner/repo` strings — when work spans orgs
4. **Local repo roots** — directories under which to scan for local commits (e.g., `~/Dev`, `~/work`). The skill walks one level deep looking for `.git/` to enumerate repos.
5. **Tracker MCP** — detect which is installed in the session (Linear, Jira, Notion, Asana, Shortcut, Trello). If multiple, ask which one this user actually files tickets in. If none, skip.
6. **Additional MCPs to query** — after the above is filled in, list the *other* MCPs currently available in the session (Slack, Discord, Google Calendar, PostHog, etc.) and ask if any should feed context into the recap. Example: Slack DMs/channels might surface conversations that explain *why* a PR was opened. Save which ones the user opts in to.

Save to `{skill_directory}/config.json`:

```json
{
  "github_login": "aturing",
  "display_name": "Alan",
  "first_person": true,
  "repo_scope": { "type": "org", "value": "acme-corp" },
  "local_repo_roots": ["~/Dev", "~/work"],
  "tracker_mcp": "linear",
  "extra_mcps": ["slack"]
}
```

Confirm with the user before saving.

### Returning user

If `config.json` exists, use it. If the user says "reconfigure" or "edit setup", re-run the setup flow.

## Resolve the time window

**First, determine today's date and current time by running:**

```bash
date '+%A %Y-%m-%d %H:%M'
```

Do NOT guess the day of the week from context or the current date string. LLMs are unreliable at day-of-week calculations. Always run the command above and use its output.

"Yesterday" at standup means **last working day**, not literal yesterday. Apply this logic to the output of the `date` command:

```
today = Mon → window starts Friday 00:00
today = Tue–Fri → window starts previous calendar day 00:00
today = Sat/Sun → window starts most recent Friday 00:00
```

The window always **ends at the current time** (now), not at midnight of the previous day. Work done earlier today (before the skill is invoked) is part of the standup. For example, if it's Tuesday 9:30am, the window is Monday 00:00 through Tuesday 09:30.

If the user specifies a window in the prompt ("since Friday", "last 3 days", "this week"), honor it. Otherwise apply the rule above. State the resolved window in the report header so the reader knows what's covered.

## Data collection

Run the following queries **in parallel** — they're independent and slow if serialized. Use ISO 8601 dates (`YYYY-MM-DD`) for the window boundaries. `{FROM}` is the start of the window (last working day). `{TO}` is **today's date** (so that any work done between midnight and now is captured).

### 1. GitHub: your authored PR activity

```bash
gh api "search/issues?q={SCOPE}+is:pr+author:{LOGIN}+updated:{FROM}..{TO}&per_page=100" \
  --jq '.items[] | {number, title, html_url, state, draft, merged_at, created_at, updated_at, body, repo: (.repository_url | split("/") | last), labels: [.labels[].name]}'
```

For each PR returned, also fetch:

- **Commits you authored in the window**:
  ```bash
  gh api "repos/{OWNER}/{REPO}/pulls/{NUMBER}/commits" \
    --jq '[.[] | select(.commit.author.email == "{EMAIL}" or .author.login == "{LOGIN}") | {sha, message: .commit.message, date: .commit.author.date}]'
  ```
- **Reviews on the PR** (to know if you addressed feedback yesterday):
  ```bash
  gh api "repos/{OWNER}/{REPO}/pulls/{NUMBER}/reviews" \
    --jq '[.[] | select(.user.login | test("\\[bot\\]$") | not) | {user: .user.login, state, submitted_at, body}]'
  ```

### 2. GitHub: reviews you gave to others

```bash
gh api "search/issues?q={SCOPE}+is:pr+reviewed-by:{LOGIN}+updated:{FROM}..{TO}&per_page=100" \
  --jq '.items[] | {number, title, html_url, repo: (.repository_url | split("/") | last), author: .user.login}'
```

For each, fetch your reviews specifically to know whether you approved, requested changes, or commented:

```bash
gh api "repos/{OWNER}/{REPO}/pulls/{NUMBER}/reviews" \
  --jq '[.[] | select(.user.login == "{LOGIN}") | {state, submitted_at, body}]'
```

### 3. GitHub: comments you left

```bash
gh api "search/issues?q={SCOPE}+commenter:{LOGIN}+updated:{FROM}..{TO}&per_page=100" \
  --jq '.items[] | {number, title, html_url, repo: (.repository_url | split("/") | last)}'
```

Deduplicate against the prior two queries — only count this PR if it wasn't surfaced as authored-by or reviewed-by you. The remaining set is PRs where you contributed *just* a comment.

### 4. Local git commits

For each configured local repo root, enumerate `*/.git/` one level deep, then for each repo:

```bash
git -C {repo_path} log --author="{LOGIN_OR_EMAIL}" \
  --since="{FROM}" --until="{TO} 23:59:59" \
  --pretty=format:'%H|%ai|%s|%b%n---'
```

These catch work that hasn't hit GitHub yet — local WIP, branches not pushed. Deduplicate SHAs against the GitHub PR commits already collected.

### 5. Deploys / release automation

For each merged PR in step 1, check whether a release workflow fired afterward:

```bash
gh api "repos/{OWNER}/{REPO}/actions/runs?created=>={MERGE_DATE}&per_page=20" \
  --jq '.workflow_runs[] | select(.name | test("release|deploy|publish"; "i")) | {name, conclusion, html_url, created_at, head_sha}'
```

Match on `head_sha` (the merged PR's merge commit SHA) or by time proximity (workflow created within ~5 min of merge). Record: did it run, did it succeed, when. If the conclusion is `failure`, surface that explicitly — a "shipped" PR that didn't actually deploy is the kind of detail standup is for.

### 6. Linked tickets (if tracker MCP configured)

For each PR collected, scan `body` and `title` for ticket references:

- Linear: `\b[A-Z]{2,5}-\d+\b` (e.g., `ENG-142`)
- Jira: same shape, configured project keys
- Notion: URLs matching `notion.so/...`
- GitHub issues: `#\d+` references resolved within the repo

Use the configured tracker's MCP to fetch each ticket's **title and status**. The title is what you use in the narrative ("the image cache eviction bug") — the ticket ID stays in the footnote.

### 7. Optional MCP context

For each opted-in extra MCP (from setup), pull anything from the time window that mentions the user or references the PRs/tickets above. Examples:

- **Slack**: messages mentioning `@{user}` or threads where they posted code-related replies during the window. Filter aggressively — birthday wishes and lunch polls are noise.
- **Calendar**: meetings tagged or named for the repos/projects involved. A "design review for X" meeting is context the standup can mention ("the morning was meetings — design review for X took an hour").

Treat MCP results as *narrative seasoning*, not primary data. If an MCP errors out or returns nothing, skip silently — the standup still works without it.

## Naming work in human terms

For every PR, commit cluster, or ticket, derive a **human phrase** that names the work. Priority order:

1. **Linked ticket title**, lowercased and trimmed (e.g., `"Image cache evicts entries on retry"` → "the image cache eviction bug" or just "image cache eviction")
2. **PR title with conventional-commit prefix stripped** (`fix(cache): LRU eviction on retry` → "fixing the LRU eviction on retry")
3. **Commit subject** if the PR has no descriptive title
4. **First meaningful file path** as a last resort (`src/cache/lru.ts` → "the LRU cache code")

The phrase goes in the prose; the PR number and ticket ID go in the refs footnote. Inline numbers belong only when the user explicitly asks ("include PR links inline").

## Narrative synthesis

This is where the skill earns its keep. The naive version of this skill enumerates events. The version worth shipping reads like a **Staff Engineer's standup**: impact-first, root-cause-aware, and honest about judgment calls.

### Write like a Staff Engineer, not a junior

The reframe that matters: a standup is not a status report on *you*. It's a status report on **the system** — what's better, who's unblocked, what risks were caught, what's still in flight and why. The work is the vehicle; the impact is the cargo.

Apply these shifts when synthesizing:

- **Lead with impact, not action.** "The X bug that's been paging us all week is fixed and deployed" beats "Fixed bug X". The reader cares that the pages stop, not that you typed.
- **Name root causes, not just symptoms.** If you debugged something, say what was actually wrong — that's the standup-worthy detail. "Found the LRU was admitting entries faster than it evicted under burst load" is what makes the team smarter; "fixed the cache" doesn't.
- **Reviews are judgment calls, not tasks.** Recast: "Approved Daniel's PR" → "Unblocked Daniel on the auth refactor — the migration plan was sound." "Requested changes on Carol's PR" → "Pushed back on Carol's caching strategy; I think the eviction model will bite us next quarter." Name what you decided and why, not just the GitHub button you clicked.
- **Connect work to systems and people.** Which team is unblocked? Which downstream service was at risk? Which on-call rotation just got quieter? Standup-readers want to map your work onto the org.
- **Acknowledge what didn't ship and why.** Half-done work and deliberate punts are part of the story. "Started the queue-sharding work but parked it after a quick spike showed the bottleneck is upstream — refocusing today" is staff-level. Silence on unfinished work reads as overpromising.
- **Forward-looking notes earn their keep.** If something you reviewed is going to bite later, say so once, plainly. The standup is the cheapest place to surface a future risk.
- **Vary sentence shape.** Don't open every beat with a past-tense verb ("Fixed... Reviewed... Addressed..."). Lead with the noun some of the time ("The auth refactor Daniel's been on landed cleanly"), the constraint ("Most of the day went to..."), or the surprise ("One thing that took longer than expected was...").

#### Before / after

The same events, written two ways. Both are accurate. Only one reads like a Staff Engineer wrote it.

**❌ Junior recap (events as a to-do list, dressed up):**

> Fixed the LRU eviction bug in the image cache and merged the PR. The release workflow deployed it. Reviewed two PRs — approved Daniel's auth refactor and requested changes on Carol's cache benchmarks. Addressed three comments on my queue refactor PR.

**✅ Staff recap (impact, causation, judgment):**

> The image-cache regression that's been paging the on-call rotation for a week is fixed and in prod — root cause was the LRU admitting entries faster than it evicted under burst load, which only surfaced because our retry policy amplifies traffic on the hot path. While that was baking, I unblocked Daniel on the auth-service refactor; the migration plan was sound and we agreed on the rollback path inline. Pushed back on Carol's cache-benchmark methodology — the workload she's measuring doesn't match what production sees, and shipping the conclusions as-is would have driven the wrong tuning decisions next quarter. My own queue refactor is in re-review after addressing the back-pressure concerns from Tuesday.

Notice: same five events, but the second version names the *consequence* of each one. The reader walks away knowing what changed about the system, not what tickets moved columns.

### Look for connections

Before writing, scan the collected data for these patterns. They're the raw material for the impact framing above:

- **Same files touched in multiple PRs** → likely one thread of work; group them and name the thread.
- **PR descriptions referencing prior PRs** ("follow-up to #478", "addresses feedback from review of #475") → causal link, weave it in.
- **Comments you left that were resolved by your own subsequent commits** → that's "addressed feedback and pushed back into review" as a single beat.
- **A review you gave that triggered changes** → that's a judgment call, not a button click. Name what you flagged and what changed.
- **A merged PR that deployed cleanly** → one beat, framed by impact ("shipped, error rate normalized" / "shipped, no rollback needed").
- **A merged PR that *didn't* deploy, or deployed and failed** → its own beat, surface explicitly. A "merged" PR that didn't reach prod is the kind of detail standup exists to catch.
- **Tickets that closed without your PR closing them** → maybe a review of yours unblocked the close; cross-reference.

### Tone

Write in past tense. First-person if `first_person: true`, otherwise use the configured display name in the third person.

Use connective tissue that conveys rhythm without literal timestamps: *most of the day*, *while that was running*, *on the side*, *between meetings*, *late afternoon*, *one thing that took longer than expected*. These cue the reader to time-of-day shape and let you order beats by importance rather than by clock.

Avoid the word "PR" in prose if you can substitute the work-name. "Shipped the image cache fix" beats "Merged the image-cache PR". Avoid "addressed feedback" without saying what the feedback *was* — "addressed the back-pressure concerns from Tuesday" tells the reader something; "addressed feedback" doesn't.

## Report format

```markdown
# Standup — {YYYY-MM-DD}
> Covering: {window_human} | {N} PRs touched | {M} reviews given | {K} commits

## Yesterday

{2-3 sentence narrative paragraph. Lead with impact: what changed about
the system, who's unblocked, what risk was caught. Not "I did X and Y" —
"The X problem is fixed and shipped; Y is unblocked; Z is now flagged
for next quarter." If the day was mostly meetings or interrupts, say so
plainly and frame what it enabled.}

## Recap

{Long-form journal section. 2-5 short paragraphs grouping events by
thread, not by source. Each paragraph is one coherent story with its
own impact line. Cross-reference where it helps — "the same auth
refactor I reviewed Tuesday, Daniel ended up shipping before EOD; the
migration ran clean."

Open paragraphs with varied shapes — not every one starts with a verb.
Lead with the noun ("The auth refactor..."), the constraint ("Most of
the morning..."), or the surprise ("One thing that took longer than
expected..."). Pure verb-first openers across every paragraph is the
junior tell.}

## For the channel

{Tight bullet list, 4-8 lines, slack-pasteable. Each bullet still
carries impact framing — what changed, what's unblocked, what's
flagged. Naked "Reviewed X" / "Approved Y" bullets are a regression
to the junior format; even compressed, the bullets should say *why
it mattered*. Names work in human terms. Deploy state inlined only
when it's notable.}

- Image-cache regression shipped — on-call rotation should stop paging
- Unblocked Daniel on auth refactor (approved after working through the rollback path inline)
- Pushed back on Carol's cache-benchmark methodology — workload doesn't match prod
- Queue refactor back in review after addressing the back-pressure concerns
- Spiked queue-sharding, parked it — bottleneck is upstream, refocusing today

## Refs

{Compact footnote with the actual identifiers, for anyone who wants to
chase a link. One line per work item.}

- image cache eviction — PR acme-corp/api#481, ENG-142, deployed
- auth refactor (Daniel) — PR acme-corp/api#478 (reviewed)
- LRU cache benchmarks — PR acme-corp/api#479 (reviewed, changes requested)
```

### Length rule of thumb

- **Yesterday paragraph**: 2-3 sentences, never more than 4. If the day was busy, summarize at a higher level rather than running long.
- **Recap section**: aim for 3 paragraphs. If you have only one beat for the day, the recap collapses into one paragraph and that's fine.
- **For the channel**: 4-8 bullets. If you have more than 8 items, you're probably listing commits as separate items when they belong grouped under one PR/thread.

### When there's nothing to report

If the window contains no activity (PTO, sick day, all-meetings day):

```markdown
# Standup — 2026-05-26
> Covering: Friday 2026-05-22 | no code activity

## Yesterday

Quiet day — nothing landed in code. {If MCPs surfaced context: "Spent the day in meetings — design review for X, planning for Y." Otherwise omit this clause.}

## For the channel

- No code shipped yesterday
```

Don't fabricate activity. An honest "quiet day" beats invented bullets.

## Edge cases

- **PRs that crossed midnight**: a PR opened Friday 23:50 and merged Monday 09:15 belongs to whichever side has the user's activity within the window. If both, mention it as a thread that carried over.
- **Reviews where you self-approved**: skip from the "reviews given" count, not interesting at standup.
- **Bot-authored PRs you reviewed** (Renovate, Dependabot): surface as a single line ("approved 3 dependency bumps"), not one bullet each.
- **Force-pushed commits**: GitHub may double-count under your authored work. Dedup by `sha`.
- **Multiple PRs on the same ticket**: collapse to one work-item in the prose, but list each PR in Refs.
- **MCP unavailable or unauthenticated**: skip silently for tracker/Slack; if `gh` itself is unavailable, tell the user to run `gh auth login` first since GitHub is the primary source.

## Output

Always render the full report inline in the conversation.

If the user asks to "post it" or "send to Slack", offer to copy the "For the channel" section specifically — the prose sections are for them, the bullets are for the team. If they configured a Slack MCP and gave a channel, offer to post directly.

If the user asks to save it, default to `./standup-{YYYY-MM-DD}.md` in the current working directory.
