---
name: intake
description: "Pre-planning ticket ingestion. Given a ticket ID or URL, reads the full ticket via MCP or CLI, follows all referenced links (Notion, Figma, GitHub, articles, etc.) using parallel subagents, synthesises a context brief, grounds it in the actual codebase via /flagrare:codebase-explore, then asks codebase-informed clarifying questions before handing off to /flagrare:atdd-plan. Works with Linear, Jira, Asana, Shortcut, Trello."
---

# Intake

Turn a ticket reference into a planning-ready context brief before `/flagrare:atdd-plan` runs. The goal: **every relevant fact is on the table and every ambiguity is resolved before a single line of implementation is planned**.

---

## Step 0 — Inventory available tools

Before anything else, check what tools and MCPs are available in this session. List every MCP whose name contains any of: `linear`, `jira`, `asana`, `shortcut`, `trello`, `notion`, `figma`, `drive`, `github`, `gitlab`, `confluence`, `browser`, `playwright`, `puppeteer`, `fetch`, `web`, `obsidian`.

Build a capability map:

```
available MCPs:   [list every matched tool]
available CLIs:   run `which linear jira shortcut gh glab notion 2>/dev/null` — note which exist
browser tools:    [any MCP or tool that can load a URL with JS/auth — playwright, puppeteer, browser MCP]
file system:      [local Obsidian vault paths if known]
```

Use this map to pick the best tool for every fetch in Steps 2–3. A browser/automation MCP beats WebFetch for pages behind login. A first-party MCP beats a browser tool. An authenticated CLI beats an unauthenticated API call.

---

## Step 1 — Parse the input

Accept any of:
- A bare ticket ID: `INT-42`, `ch12345`, `PROJ-99`
- A full URL: `https://linear.app/…`, `https://company.atlassian.net/…`
- A plain-text description pasted inline — treat as the ticket body directly, skip Steps 2–3

Identify the platform:

| Signal | Platform |
|---|---|
| `linear.app` URL or `[A-Z]{2,}-[0-9]+` | Linear |
| `atlassian.net/jira` URL | Jira |
| `app.asana.com` URL | Asana |
| `app.shortcut.com` URL or `ch[0-9]+` | Shortcut |
| `trello.com` URL | Trello |

If the platform is ambiguous, ask before proceeding.

---

## Step 2 — Read the ticket

Spawn a **Ticket Reader** subagent with `model: "sonnet"` and this brief:

> Read the full ticket [ID/URL] and return: title, description, acceptance criteria, labels/tags, priority, assignee, linked issues, attached files, and every URL mentioned in the body or comments.
>
> Use the best available tool in this order:
> 1. MCP tool for the platform (e.g. `mcp__linear__getIssue`, `mcp__jira__getIssue`, `mcp__asana__getTask`, `mcp__shortcut__getStory`)
> 2. Platform CLI (`linear`, `jira`, `shortcut`) — check if available with `which <cli>`
> 3. WebFetch on the ticket URL directly
>
> Return raw structured output. Do not summarise or interpret.

Wait for the subagent. If it returns an error (no MCP, no CLI, auth required), surface it and ask the user to paste the ticket body manually before continuing.

---

## Step 3 — Follow all references in parallel

Parse the ticket output for every linked resource. Spawn one **Reference Reader** subagent per resource, all in parallel, using `model: "sonnet"`. Each subagent uses the best tool from the capability map built in Step 0:

| Resource type | Preferred tool | Fallback |
|---|---|---|
| Another ticket (same or different platform) | Ticket Reader subagent (as in Step 2) | — |
| Notion page | `mcp__notion__*` MCP | Browser MCP → WebFetch |
| Figma file / frame | `mcp__figma__*` MCP | Browser MCP → WebFetch |
| GitHub PR / issue / file | `gh` CLI or `mcp__github__*` | WebFetch |
| GitLab MR / issue | `glab` CLI or `mcp__gitlab__*` | WebFetch |
| Google Drive / Docs | `mcp__drive__*` MCP | Browser MCP → WebFetch |
| Confluence page | `mcp__confluence__*` MCP | Browser MCP → WebFetch |
| Obsidian note | Read from local filesystem path | WebFetch if it is a published URL |
| Any other URL (articles, docs, specs, API refs) | Browser MCP (handles JS-heavy pages) | WebFetch |

Pass each subagent the relevant section of the capability map so it knows what is available without re-discovering it.

Each Reference Reader subagent brief:

> Fetch [URL / reference] and return the content most relevant to a software engineering planning session. Extract: key decisions, requirements, constraints, design specs, open questions. Summarise to ≤300 words — keep specifics (names, numbers, states) verbatim; cut filler.

Collect all results. If a resource is inaccessible (auth wall, 404, private), note it explicitly rather than silently skipping.

---

## Step 4 — Synthesise the context brief (without questions yet)

Merge ticket + all reference content into this structure:

```
Context Brief — [Ticket ID]: [Title]

Platform: [Linear / Jira / …]    Priority: [P0–P3 / Critical / …]    Assignee: [name]

## What
[1–3 sentences: what is being built or fixed]

## Why
[1–2 sentences: business or user motivation from ticket + linked docs]

## Acceptance Criteria
[Verbatim or lightly cleaned list. If absent, flag as ⚠ undefined — do not invent.]

## Constraints & Dependencies
[Technical constraints, blocked-by tickets, platform requirements, performance budgets]

## Referenced Material
[One line per followed reference: what it contributed]

## Codebase Findings
[Populated by Step 4.5 below — leave empty for now]

## Open Questions
[Everything underspecified, contradictory, or missing from the above]
```

---

## Step 4.5 — Ground the brief in the codebase

Before asking questions, see what the code actually says. Questions asked without codebase grounding are abstract; questions asked *after* exploration are specific and unblock real ambiguities ("the utility you'd want already exists at `src/x.ts` — extend it or replace it?").

### When to skip

Skip codebase grounding when any of these is true:

- `git rev-parse --show-toplevel` fails — not in a repo
- The repo has no source files (docs-only, empty, pre-code project). Heuristic: `git ls-files | grep -vE '\.(md|txt|json|ya?ml|toml|gitignore|cff)$' | head -1` returns nothing
- The user explicitly says "skip exploration" / "rough intake only"
- The ticket is purely process (e.g. `[INFRA] rotate AWS keys`) and exploration adds no value

### Otherwise

Invoke `/flagrare:codebase-explore` with the `## What` section as input plus a one-paragraph summary derived from the brief. Capture the returned findings — file paths with line numbers, existing utilities, prior branches/PRs, related patterns.

Populate the brief's `## Codebase Findings` section with the most planning-relevant items (≤8 bullets — full exploration output is fine for the consuming skill but the brief stays scannable).

If the exploration surfaces new ambiguities (e.g., "two utilities do similar things — which is canonical?"), add them to `## Open Questions`.

---

## Step 5 — Ask codebase-informed clarifying questions

From Open Questions, select the **3–5 most blocking** — things that, if unanswered, would force the plan to make assumptions or revisit scope mid-build.

Now that the brief is codebase-grounded, prefer concrete questions over abstract ones:

- "I see `src/billing/quote.ts:84` already handles the discount math — should the new flow extend it or fork it?" (not: "where should the discount logic live?")
- "The Figma spec shows a 3-step wizard but `src/onboarding/wizard.tsx` is currently 2 steps — adapt the existing component or build new?"
- "`INT-41` (which this depends on) is not merged yet — plan against current API or the incoming one in branch `feat/int-41`?"

Do not ask about things inferable from the ticket. Do not ask for information already in the brief or codebase findings.

### How to ask — use the AskUserQuestion tool, never freeform narration

**REQUIRED:** when you have blocking questions, ask them via the `AskUserQuestion` tool, not as prose. Freeform "I'd like to confirm X..." text leaves the user without a clear answering surface and frequently results in the model stopping with no answer received.

Batch all 3–5 questions into a single `AskUserQuestion` invocation. For each question, supply 2–4 distinct options when the choice is genuinely bounded (e.g., "extend the existing utility / fork it / wrap it / replace it"). Open-ended judgement calls without obvious options should be phrased as a question with one most-likely option plus alternatives.

After the user answers, fold answers into the brief and clear Open Questions before proceeding to Step 6.

### If there are no blocking questions

If the codebase-grounded brief is complete and no blocking ambiguity remains, **do not silently proceed**. Present a short overview to the user — 4–6 lines summarising what the ticket is, what the code currently does in that area, and what the plan will most likely need to build — and then explicitly prompt for the next step (see Step 6).

---

## Step 6 — Present overview and prompt for next step

Once the brief is complete (Open Questions resolved, or explicitly deferred by the user), **always end intake with a tool-driven next-step prompt** — exactly like plan mode ends with an accept/reject tool, not prose.

Present:

1. **Overview** — 4–6 lines: what the ticket is, the codebase context the plan will work within, and what's now resolved. Skip if the user just answered clarifying questions (they have the context fresh; don't repeat it).
2. **Next-step prompt** — issue an `AskUserQuestion` tool call. This is the same interaction shape as plan-mode's accept-plan tool: the user gets a discrete set of buttons, picks one, and the flow continues without freeform typing. Do NOT phrase this as a prose question — that produces ambiguity and frequently ends the turn with no answer captured.

   Intake's natural successor is `/flagrare:atdd-plan`. The brief is built specifically to be planning input, so the prompt is a simple two-way:

   - **Proceed to `/flagrare:atdd-plan`** (Recommended): pass the brief as opening context. The plan skill runs its own `/flagrare:codebase-explore` pass; intake's findings are additive input.
   - **Stop here**: return control to the user with the brief saved/printed for later use.

   Do NOT offer `/flagrare:ticket-creator` or `/flagrare:tdd-writer` here — those run *before* intake in different workflows (decomposing specs into tickets, drafting design docs for new multi-week projects). They are not downstream of a single-ticket intake.

If invoked through `/flagrare:work-prep`, skip the prompt and proceed directly to `/flagrare:atdd-plan` — work-prep already decided the next step. (Detect this by checking whether the prior message indicated work-prep orchestration.)

Never end intake with a context dump and silence. The user should always know what happens next and have a button to direct it — same UX contract as the plan-mode accept tool.

---

## Anti-patterns

- Don't summarise the ticket without reading it — "I assume this means X" is not intake.
- Don't spawn a subagent per sentence — one per distinct resource (ticket, Notion page, Figma frame, article).
- Don't skip inaccessible references silently — note them, they may be critical.
- Don't ask more than 5 clarifying questions — prioritise the blockers; defer the rest to `/flagrare:atdd-plan`'s gap review.
- Don't proceed to `/flagrare:atdd-plan` if Acceptance Criteria are still ⚠ undefined — resolve them first.
- Don't invent acceptance criteria to fill the gap — flag the absence and ask.
- **Don't ask clarifying questions as prose.** Use the `AskUserQuestion` tool with options. Prose questions cause the turn to end with no answer captured.
- **Don't end intake with a context dump and silence.** Always close with a tool-driven next-step prompt — same UX contract as plan mode's accept tool. The user must have a button, not a typing prompt.

---

## Flow position

```
/flagrare:intake [ticket ID or URL]
     ↓ subagents read ticket + all references in parallel
     ↓ /flagrare:research-catalog  ← log every external source before synthesising
     ↓ context brief synthesised (without questions)
     ↓ /flagrare:codebase-explore  ← ground the brief in actual code
     ↓ codebase-informed clarifying questions answered
     ↓
/flagrare:atdd-plan  ← receives the codebase-grounded context brief
     ↓ /flagrare:codebase-explore  ← runs its own thorough pass (stays standalone-callable)
     ↓ ATDD plan produced
     ↓
[implementation]
     ↓
/flagrare:staleness-audit
     ↓
/flagrare:implementation-review
     ↓
git commit
     ↓
/flagrare:release-check
```
