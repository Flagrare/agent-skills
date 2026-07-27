---
name: senior-scan
description: Scan the org's communication surfaces (chat like Slack or Teams, open PRs, RFC docs and design docs, ticket threads, whichever MCPs are connected) for high-leverage discussions the user should weigh in on, decisions still being formed, people stuck or circling, questions squarely inside the user's domains, cross-team changes touching systems they own or depend on. Built for engineers working toward promotion, it hunts opportunities to operate at the next level (influence beyond assigned work), ranks them by leverage and credibility, drafts replies in the user's own voice for approval, and logs posted contributions as promotion evidence that /flagrare:brag-doc can later consume. Use whenever the user says "senior scan", "promo scan", "what needs my attention", "where should I weigh in", "anything I should jump into", "scan slack", "scan PRs", "catch me up on what's happening", or any variant of "where can I have the most impact today", even when the skill isn't named. Also trigger when the user talks about wanting more visibility, more scope, or operating above their level.
---

# Senior Scan

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

## Setup (first run only)

Config lives in the shared **`~/.claude/skills/flagrare/config.json`**: skill-agnostic keys (GitHub login, display name, repo scope) at the top level, senior-scan keys under `skills["senior-scan"]`. Mutable files live in **`~/.claude/skills/flagrare/senior-scan/`** (`state.json`, `contributions.log.md`, `voice.md`), outside the plugin tree so they survive plugin updates.

In Bash, expand `~` explicitly and `mkdir -p "$HOME/.claude/skills/flagrare/senior-scan"` before writing.

If `skills["senior-scan"].onboarding_complete` is not `true`, run onboarding. Reuse any top-level keys another flagrare skill already collected (ask only for what's missing), and only write the `skills["senior-scan"]` block plus missing top-level keys; leave other skills' blocks untouched.

### Onboarding

The interview is half discovery, half confirmation: propose from real data wherever possible so the user is confirming lists, not composing them from memory.

1. **Identity.** GitHub login (detect via `gh api user --jq '.login'` or the GitHub MCP `get_me`, confirm) and repo scope (`org:<name>`, `user:<login>`, or explicit `owner/repo` list). Chat handle: look the user up with the chat MCP's user search, confirm the match.
2. **Career target.** Ask current level and target level, then which next-level behaviors to hunt for. Offer defaults by transition and let the user edit or paste their company ladder's actual language:
   - toward **senior**: influence beyond assigned tickets, unblocking others, owning technical decisions in their domain, raising the quality bar
   - toward **staff**: cross-team leverage, setting direction, connecting efforts that don't know about each other, derisking big decisions early
   The chosen behaviors become the definition of the Stretch axis (see Scoring), so they should be concrete.
3. **Domains of real standing.** Spawn a discovery agent over the user's recent GitHub activity (authored PRs, reviews given, comment threads) to propose the areas where they demonstrably know things: systems, failure modes, conventions. Present the proposal; the user confirms, trims, adds. For each domain also collect 2-4 search keywords. Credibility scoring depends on this list being honest, so tell the user: list what you actually know, not what you want to know.
4. **Surfaces.** List the MCPs connected in the session that can read a surface (chat, code review, docs, tickets) and ask which should feed the scan, the same detect-and-opt-in move `/flagrare:standup-report` uses for `extra_mcps`. For each chosen surface, collect its scope by proposing from real data:
   - **chat**: channels, proposed via channel search using team names and domain keywords; include team channels, eng-wide channels, and incident/announcement channels
   - **code review**: repos, proposed from the user's recent activity within the repo scope
   - **docs**: spaces, databases, or folders where RFCs and design docs live, proposed via the doc MCP's search using the domain keywords
   - **tickets**: projects or teams whose comment threads matter, proposed the same way
5. **Audience (optional).** Names whose visibility matters for the promotion case: manager, senior/staff engineers, adjacent team leads. Powers the Audience score; without it that axis defaults to 1 and the skill says so.
6. **Voice.** Fetch a sample of the user's own recent writing (their Slack messages, their PR review comments, not other people's), distill 5-8 observed rules (sentence length, hedging style, formality, emoji use, how they disagree), and write them to `voice.md`. Show the rules for confirmation. If no sample is reachable, fall back to the generic drafting rules below and note it.

Save, then show the full config summary for one final confirmation and set `onboarding_complete: true`.

```json
{
  "github_login": "aturing",
  "display_name": "Alan",
  "repo_scope": "org:acme-corp",
  "skills": {
    "senior-scan": {
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
    }
  }
}
```

Re-run any onboarding step when the user says "reconfigure", or when they say the scan keeps looking in the wrong places.

## Workflow

### 1. Load state and window

Read `state.json` (`{ "last_run": iso8601, "seen": [{ "id", "source", "surfaced_at", "status" }] }`). The scan window is `last_run` to now; if no state exists, default to the last 48 hours, capped at 7 days. Items already in `seen` are only re-surfaced if they escalated: a new decision point, a new unanswered question, a thread reopened.

### 2. Sweep in parallel

Spawn **one read-only sweep subagent per configured surface**, all in the same message so they run concurrently. Each gets its surface's scope, the domain map with keywords, the exclusions, the user's identity (so their own posts are skipped), and the time window.

Every sweep hunts the same four signals: (a) a decision still being formed (architecture, API contracts, migrations, process); (b) a question nobody has answered well, or a thread going in circles; (c) a discussion inside the user's domains that is missing context the user has; (d) work from other teams that touches systems the user owns or depends on. And every sweep returns the same shape, raw findings only, no ranking: location and link, participants, a 2-3 sentence summary, matched signal(s), and the specific gap the user could fill.

**Chat sweep (reference: Slack).** Read recent activity in each configured channel, follow interesting threads, and additionally run 2-3 keyword searches from the domain map, since relevant discussions happen outside configured channels. Ignore social chatter, resolved threads, FYI-only announcements, and threads where the right people are already converging.

**Code-review sweep (reference: GitHub).** List open PRs in the configured repos updated within the window and not authored by the user, then read the promising ones including review threads. Also hunt for: PRs whose changed paths touch the user's domains, and approaches carrying a risk the discussion hasn't caught, judged against the domain map's known failure modes. Ignore approved-and-converging PRs, trivial changes, and PRs where requested changes are simply in progress.

**Generic sweep (any other surface: docs, tickets, other chat platforms).** Enumerate items in scope updated within the window (pages, tickets, threads), read the ones with active human discussion, and apply the four signals. On docs surfaces, treat unresolved comment threads and open review periods on RFCs and design docs as prime candidates: they are decisions with explicit windows. Ignore items with no discussion, resolved threads, and pure status updates.

### 3. Score and cut

Score each candidate 0-2 on five axes:

- **Leverage**: would weighing in change the outcome, or just add a voice? A decided thread scores 0.
- **Credibility**: does the user have specific knowledge, context, or ownership the participants lack? Generic "good point" opinions score 0.
- **Stretch**: does this exercise one of the configured target behaviors, beyond the user's assigned lane? Routine work in their own tickets scores low.
- **Audience**: will configured audience people (or their equivalents) see the contribution? Defaults to 1 when no audience is configured.
- **Timing**: is the window still open? A decision landing today scores 2; something simmering for weeks scores 1.

**Hard filter first:** drop anything with Leverage 0 or Credibility 0, regardless of the other axes. That is the anti-performative rule, and it is not negotiable, it protects the user's reputation. Then rank survivors by total and keep at most 5. Dedupe against `state.json` before presenting.

### 4. Present the digest

The user has not read these threads. Contextualize fully; never assume they know what a thread is about.

```
## Senior scan: <date>, window <X>h  <note any configured surface skipped because its MCP was unavailable>

### 1. <One-line headline of the opportunity>
**Where:** <channel or repo#PR, as a link>
**What's happening:** <2-4 sentences: who, what's being discussed or changed, where it stands>
**Why you:** <the specific gap the user fills, plus which target behavior this exercises>
**Suggested angle:** <one sentence: the substance of what to say>
**Draft:**
> <draft reply or review comment, following the drafting rules>

(repeat per item)

### Skipped but notable
- <one line each for 2-5 near-misses and why they were cut; this keeps the filter honest and tunable>
```

### 5. Drafting rules

Read `voice.md` first if it exists; its observed rules win over the generic ones. Generic floor, applied always:

1. **Short and direct.** A few sentences, no preamble, no "Great discussion!", no wrap-up flourish.
2. **No LLM tells.** No em-dashes, no "aligns with", no rule-of-three constructions, no self-congratulation.
3. **First person, explicit.** "I ran into this", never "Ran into this".
4. **Hedge pushback collaboratively, without interrogating.** State the concern plainly with its evidence and admit possible missing context. A closing question is for genuine uncertainty, when you actually need the author's context to resolve the point, not a mandatory sign-off: ending every draft with "does that match your understanding?" reads as a tic, and a faux-question that is really an assertion ("am I reading this right that this is unused?") reads passive-aggressive, which is worse than asserting. When the evidence is on the table and you are confident, say the thing and stop.
5. **Contextualize references.** Never a bare ticket number; say what the ticket is with the key in parentheses.
6. **Cite PRs and commits, not people.** Explaining where a behavior came from means pointing at the PR or SHA, never naming who broke it.
7. **Substance first.** Every draft must contain the specific fact, risk, or suggestion that justified surfacing the item. If someone without the user's context could have written the draft, the item fails the credibility bar: cut it instead of shipping filler.

**Never post anything anywhere.** Every draft waits for the user's explicit approval of that specific message. Posting without it is the one unforgivable failure of this skill.

### 6. Update state and the evidence trail

After presenting, write `state.json`: update `last_run`, append surfaced items with `status: "surfaced"`.

When the user approves and posts a contribution (or says they handled it), set that item's status to `"contributed"` and append to `contributions.log.md`:

```
- <date> | <link> | <one sentence: what the contribution was and what it changed> | behavior: <target behavior exercised>
```

This log is the promotion evidence trail, the lagging indicator made legible. When the user later runs `/flagrare:brag-doc` or builds a promo packet, point them at it; brag-doc should treat it as a first-class source.
