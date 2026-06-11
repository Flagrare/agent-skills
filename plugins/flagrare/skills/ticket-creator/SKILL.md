---
name: ticket-creator
description: "Create well-structured tickets as reviewable markdown files, then push to any tracker (Jira, Linear, Trello, Asana, Shortcut) via MCP or CLI after user review. Grounds each ticket in actual code by calling /flagrare:codebase-explore before drafting, and polishes the Context section via /flagrare:write-docs. Use when the user asks to create tickets, file bugs, write stories, create tasks, build a backlog, or convert specs/TDDs into implementation tickets."
---

# Ticket Creator

Create tickets as **reviewable markdown files** first. Present them for review. Only push to the tracker when the user explicitly approves.

---

## When to Use

- User asks to create tickets, file a bug, write a story, create tasks
- User wants to build a backlog from a spec or TDD
- User says "create tickets for this", "break this into tickets", "file a bug"
- User provides a spec/TDD and wants implementation tickets

---

## Step 0: Detect the Tracker

Before anything else, determine which tracker to target.

**Detection order:**

1. User explicitly says (e.g. "create a Linear issue", "file in Jira")
2. Check available MCP tools: scan for `linear`, `jira`, `asana`, `shortcut`, `trello` in tool names
3. Check available CLIs: `which linear jira gh shortcut 2>/dev/null`
4. Check the project for clues: `.linear/`, `atlassian.net` in configs, existing ticket references in git history
5. Ask the user if ambiguous

**Tracker capability map:**

| Tracker | MCP tool pattern | CLI | Ticket ID pattern |
|---------|-----------------|-----|-------------------|
| Jira | `mcp__*atlassian*__*Jira*` | `jira` | `[A-Z]+-[0-9]+` |
| Linear | `mcp__*linear*__*` | `linear` | `[A-Z]+-[0-9]+` |
| Shortcut | `mcp__*shortcut*__*` | `shortcut` | `ch[0-9]+` / `sc-[0-9]+` |
| Asana | `mcp__*asana*__*` | - | numeric ID |
| Trello | `mcp__*trello*__*` | - | card URL |
| GitHub Issues | `gh issue create` | `gh` | `#[0-9]+` |

Record which tools are available. Use the best one when it's time to push.

---

## Step 0.5: Ground the Ticket in Code (Pre-Draft)

Before drafting any ticket, ground it in the actual codebase if one exists. An engineer picking up an ungrounded ticket has to repeat the codebase exploration that this skill could have done once. Tickets that point at specific files and reuse-candidates are dramatically more useful than tickets that gesture vaguely at "the relevant area".

### When to skip

Skip codebase grounding when any of these is true:

- `git rev-parse --show-toplevel` fails, not in a repo
- The repo has no source files (docs-only, empty, pre-code project). Heuristic: `git ls-files | grep -vE '\.(md|txt|json|ya?ml|toml|gitignore|cff)$' | head -1` returns nothing
- The user explicitly says "rough draft", "skip exploration", "no code yet"
- The ticket is purely process (e.g. `[INFRA] add CODEOWNERS file`, `[DEVOPS] rotate AWS keys`) and exploration would add no value, use judgement

### How to ground (single ticket)

Call `/flagrare:codebase-explore` with the ticket's working title and a one-paragraph description of what it covers. Capture the returned findings: file paths with line numbers, related patterns, existing utilities that could be reused, prior branches/PRs.

These findings populate a new ticket subsection (see template updates below).

### How to ground (backlog / spec → tickets)

For multi-ticket flows (spec/TDD decomposition), dispatch N parallel `/flagrare:codebase-explore` agents, one per candidate ticket, in a **single message** with multiple `Agent` tool calls using `model: "sonnet"`. Each agent gets that candidate's `{title, summary}` and returns its findings independently. Wall-clock stays bounded regardless of backlog size.

Do NOT run codebase-explore sequentially for backlog flows. The parallelism is the whole point, emit all `Agent` calls in one message so the runtime can execute them concurrently.

---

## Output Format

Tickets are written as numbered markdown files in a backlog folder.

### File Structure

```
docs/backlog/
  INDEX.md           # Overview, sequencing, summary table
  00-epic.md         # Epic/project definition (if creating a new one)
  01-short-slug.md   # First ticket
  02-short-slug.md   # Second ticket
  ...
```

### File Naming

- `NN-kebab-case-slug.md` where NN is zero-padded sequence number
- Slug is a short, descriptive kebab-case version of the summary
- Epic/project is always `00-epic.md`

### Single Ticket Metadata Block

```markdown
# [PREFIX] Summary here

**Type:** Story | Task | Bug
**Priority:** High | Medium | Low | Critical
**Parent:** PROJ-123
**Tracker:** Jira | Linear | Shortcut | Asana | Trello | GitHub
```

### INDEX.md Structure

```markdown
# [Backlog Name]

**Epic/Project:** [KEY or "to be created"]
**Source:** `path/to/spec-or-tdd.md`
**Tracker:** [Jira | Linear | etc.]
**Total tickets:** N

## Suggested Sequencing

[ASCII tree or diagram showing phases and parallelism]

## Summary

| # | Summary | Type | Status |
|---|---------|------|--------|
| 01 | [PREFIX] First ticket summary | Story | draft |
| 02 | [PREFIX] Second ticket summary | Task | draft |

## Open Questions (optional)

## Blockers (optional)
```

---

## Title Convention

Titles follow: `[PREFIX] Summary`

**Common prefixes:** `[FE]`, `[BE]`, `[FE/BE]`, `[SPIKE]`, `[E2E]`, `[INFRA]`, `[DEVOPS]`

Optionally include service name: `[BE][billing-service] Summary`

Summary should be concise and action-oriented. If you have seen the ticket before, it should fully remind you what it is about.

---

## Issue Types

| Type | When to Use |
|------|-------------|
| **Story** | New user-facing features. Value to customers (not just engineering) |
| **Task** | Engineering work without direct customer value (refactors, infra, test coverage) |
| **Bug** | Defects, errors, incorrect behavior |
| **Epic/Project** | Groups related Stories/Tasks/Bugs into a larger deliverable |

---

## Ticket Body Templates

Each template has an optional grounding subsection populated from `/flagrare:codebase-explore` findings (Step 0.5). The heading varies by type but the content format is the same: file paths with brief annotations, existing utilities, prior branches. Omit the subsection entirely if codebase grounding was skipped.

### Feature Tickets (Story/Task)

```markdown
## Goal
[One-liner: what this delivers and why it matters.]

## Context
[Assume zero prior context. Explain what part of the project, what needs to change, end result. Link TDD/spec if available.]

## Existing Patterns (optional: from codebase-explore)
- `path/to/file.ts:42`, the function this touches today
- `path/to/utility.ts`, existing helper to reuse instead of writing fresh
- `prior-branch/feat-x`, abandoned approach, see PR #142 for why

## What needs to happen (optional, if implementation is known)
[Bullet list of specific changes: files, components, endpoints.]

## Acceptance Criteria
* [Specific, testable criterion]
* [Specific, testable criterion]
```

### Bug Tickets

```markdown
## Context
[What is happening vs what should happen. How discovered. Include IDs, threads, screenshots.]

## Suspect Code (optional: from codebase-explore)
- `path/to/file.ts:128`, handler where the bad behavior originates
- `path/to/validator.ts:64`, likely missing the guard for this input shape

## Steps to Reproduce (if known)
1. Step 1
2. Step 2

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Acceptance Criteria
* [Specific fix criterion]

## Environment
[dev/prod/both, platform, browser, app version]

## Reference (optional)
[Logs, code links, related tickets.]
```

### Spike Tickets

```markdown
## Goal
[What question or problem needs investigation.]

## Context
[Background on why the spike is needed.]

## Prior Work (optional: from codebase-explore)
- `path/to/experimental.ts`, partial attempt from Q1
- `feat/spike-x` branch, abandoned, see PR #87 discussion for blockers

## Acceptance Criteria
* Document findings in [location]
* Evaluate LOE for [approaches]
* Recommend an approach with tradeoffs

## Reference
[Links to existing docs, related systems.]
```

---

## Polish the Context (Post-Draft)

After the draft is assembled with codebase findings, polish the **Context section only** by invoking `/flagrare:write-docs` with the draft Context as input.

The polish applies write-docs's craft layer to the Context: reader-situation-first opening, concrete file references inline (drawn from the grounding subsection), prose over bullets where causality matters, voice consistent across tickets.

Sections NOT polished, they stay mechanical:

- Metadata block, fixed format
- Acceptance criteria, testable bullets; prose would blur them
- Environment, References, Steps to Reproduce, factual lists

**Skip polish when:** the user says "rough draft" / "skip polish" / `--rough`, or codebase grounding was skipped (without code references, there is little for write-docs to humanize).

---

## Sizing

Tickets should be **2-3 days of work**. If larger, break up.

---

## Acceptance Criteria Best Practices

Specific and testable:
- "API returns 201 on successful creation" (not "user can be created")
- "Disabled items render greyed-out with tooltip" (not "disabled state works")

---

## Workflow: Single Ticket

1. Determine issue type, prefix, parent, and tracker.
2. Ask for the backlog folder path if not obvious from context.
3. **Ground in code**: if conditions allow (see Step 0.5), call `/flagrare:codebase-explore` with the ticket's working title and description. Capture findings.
4. Write the `.md` file with the next available sequence number, including the grounding subsection if applicable.
5. **Polish the Context**: if grounding ran and polish wasn't opted out, call `/flagrare:write-docs` on the Context section. Replace the draft Context with the polished version. **Do not end your turn here**: a polished ticket file looks finished, but steps 6-7 still remain. Continue in the same turn.
6. If an `INDEX.md` exists, update it.
7. Present the result, see *Presenting the result* below (tool-driven close, not prose).

## Workflow: Spec/TDD to Backlog

1. **Read the source** - spec, TDD, or wiki page.
2. **Analyze and decompose** into 3-15 implementation tickets. Consider:
   - Technical layers (BE, FE, Database, Infra)
   - Dependencies and sequencing
   - Sizing (2-3 days each)
3. **Parallel codebase grounding**: if conditions allow (Step 0.5), dispatch N parallel `/flagrare:codebase-explore` agents (one per candidate ticket) by emitting N `Agent` tool calls with `model: "sonnet"` in a single message. Wait for all results before drafting.
4. **Draft and polish each ticket**: for each ticket: assemble with grounding findings, then call `/flagrare:write-docs` on the Context section (skip if grounding was skipped or polish opted out).
5. **Write all files:**
   - `00-epic.md` (if creating a new Epic/Project)
   - `NN-slug.md` for each ticket
   - `INDEX.md` with sequencing, summary table, open questions, blockers
6. Present the result, see *Presenting the result* below (tool-driven close, not prose).

---

## Presenting the result

After the file(s) are written and the index updated, **close with a tool, not prose.** A drafted ticket (or backlog) reads as "done," so ending with a prose "here's the ticket, let me know" frequently stops the turn before the user can act (the stall pattern in [`docs/research/2026-06-11-claude-code-goal-anti-stall.md`](../../../../docs/research/2026-06-11-claude-code-goal-anti-stall.md)). Issue an `AskUserQuestion` with options:

- **Push to the tracker** (Recommended when a tracker was detected in Step 0), proceed to *Workflow: Push to Tracker*.
- **Revise first**: collect changes, edit the file(s), re-present.
- **Leave as local files**: stop here; the markdown is the deliverable.

---

## Workflow: Push to Tracker

**Only when the user explicitly approves** (e.g. "push these", "create these", "looks good, go ahead").

### Jira

1. Call `getAccessibleAtlassianResources` to get cloud ID
2. Ask for project key if not known. Use `getVisibleJiraProjects` if needed
3. Call `getJiraProjectIssueTypesMetadata` to discover available issue types
4. Create Epic first (from `00-epic.md`) if needed. Capture the key.
5. Create child tickets sequentially, setting `parent` to Epic key
6. Update `.md` files with the assigned key

### Linear

1. List teams/projects via Linear MCP or CLI (`linear team list`)
2. Ask for team if not known
3. Create project/milestone if `00-epic.md` exists
4. Create issues with `linear issue create` or MCP equivalent
5. Set parent/project relationships
6. Update `.md` files with the assigned identifier

### GitHub Issues

1. Create milestone if `00-epic.md` exists
2. For each ticket: `gh issue create --title "..." --body "..." --milestone "..."`
3. Add labels matching the type (bug, enhancement, task)
4. Update `.md` files with issue numbers

### Shortcut

1. List projects via Shortcut MCP or CLI
2. Create epic if `00-epic.md` exists
3. Create stories with appropriate workflow state
4. Update `.md` files with story IDs

### Asana / Trello

1. Identify target project/board via MCP
2. Create section/list for the epic if needed
3. Create tasks/cards for each ticket
4. Update `.md` files with task/card IDs

### After Push (all trackers)

Update each `.md` file metadata:
```markdown
**Ticket:** PROJ-250
**Status:** created
```

Update `INDEX.md` summary table status from `draft` to `created` with the ticket key.

Present a summary with all created ticket keys/URLs.

---

## Anti-patterns

- Don't create tickets directly in the tracker without writing .md files first.
- Don't push without explicit user approval. Always review first.
- Don't skip acceptance criteria. Every ticket needs them.
- Don't write tickets larger than 3 days of work. Break them up.
- Don't use vague summaries. The title alone should remind you what it is about.
- Don't assume the project/team. Ask if unclear.
- Don't hard-code a single tracker. Detect from context.
- Don't skip codebase grounding when a codebase exists. A ticket pointing at `path/to/file.ts:42` is dramatically more useful than one gesturing at "the relevant area".
- Don't run `/flagrare:codebase-explore` sequentially for a backlog flow. Emit all `Agent` tool calls in a single message, the runtime executes them concurrently. N tickets must take roughly the same wall-clock as 1.
- Don't polish acceptance criteria, environment, or metadata via write-docs. Those sections are mechanical by design; prose-ifying them blurs the testability.
