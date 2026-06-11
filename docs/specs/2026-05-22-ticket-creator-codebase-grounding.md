# Ticket Creator: Codebase Grounding + Humanized Prose

**Date:** 2026-05-22
**Status:** Approved
**Affected skill:** `plugins/flagrare/skills/ticket-creator/SKILL.md`

## Why

Tickets today are well-structured but ungrounded. The Context section reads like a PM wrote it from requirements alone, abstract phrases like "the relevant area" and "the appropriate handler" without ever pointing at the file the reader will actually touch. The result is the engineer picking up the ticket has to re-do the codebase exploration that ticket-creator could have done once at draft time.

Two improvements close that gap: (1) call `codebase-explore` before drafting to find specific file paths and existing patterns, and (2) call `write-docs` to rewrite the Context section in human-voice prose.

## Pipeline

**Single ticket:**

```
detect tracker  →  type + prefix + parent  →  [codebase-explore?]  →
draft from template + findings  →  [write-docs polish on Context?]  →
review  →  push
```

**Spec/TDD → backlog:**

```
read source  →  decompose into N candidates {title, summary}  →
dispatch N parallel codebase-explore agents (one per candidate)  →
for each: draft + polish  →  write files + INDEX.md  →  review  →  push
```

The new orchestration is the bracketed steps. Everything else, tracker detection, file naming, INDEX structure, push flow, is unchanged.

## When `codebase-explore` runs

Conditional, not always:

| Condition | Call codebase-explore? |
|---|---|
| `pwd` is a git repo with source files | yes |
| Pre-code project, empty repo, docs-only | no |
| User explicitly says "skip exploration" / "rough draft only" | no |
| Ticket is purely process (e.g. "[INFRA] add CODEOWNERS file") | no, at the model's discretion |

Detection: `git rev-parse --show-toplevel` succeeds AND the repo contains at least one source file (heuristic: `git ls-files | head -50` produces non-doc/non-config output).

## New ticket body subsection

A new optional subsection populated from `codebase-explore` findings, framed per ticket type:

| Ticket type | Subsection heading |
|---|---|
| Bug | `## Suspect Code` |
| Story / Task (feature) | `## Existing Patterns` |
| Spike | `## Prior Work` |

Content format:

```markdown
## Existing Patterns
- `path/to/file.ts:42`, the function this touches today
- `path/to/utility.ts`, existing helper to reuse instead of writing fresh
- `prior-branch/feat-x`, abandoned approach from Q1, see PR #142 for why
```

Placement: between `## Context` and `## What needs to happen` (for features) or between `## Context` and `## Steps to Reproduce` (for bugs).

The subsection is omitted entirely when `codebase-explore` is skipped.

## `write-docs` polish

Called on the **Context section only**, after the initial draft. The remaining sections stay mechanical:

- Metadata block, fixed format, no prose
- Acceptance criteria, testable bullets, write-docs would only blur them
- Environment, References, purely factual

The polish rewrites Context to:
- Open with the reader's situation (an engineer picking up the ticket)
- Reference the specific files from the new subsection inline
- Prefer prose over bullets where causality matters
- Stay terse, write-docs's own "scale to complexity" rule applies

Opt-out: user says "skip polish" / "rough draft only" / `--rough` (informal flag in user prompt).

## Parallel dispatch for backlog

For spec/TDD → backlog, after decomposing into N candidate tickets, dispatch N parallel `codebase-explore` agents in a single message with multiple `Agent` tool calls. Each agent receives one candidate's `{title, summary}` and returns its findings independently. No external skill dependency, the parallelism is a property of how tool calls in a single message are executed.

Wall-clock stays bounded regardless of backlog size. The draft + polish pass per ticket may also parallelize at the implementer's discretion, but is not required by this spec.

## Backwards compatibility

Additive only. The skill's existing behavior, template-driven drafts, tracker push flow, INDEX.md structure, file naming, is unchanged.

- If `codebase-explore` would add no value → skip, fall back to today's flow exactly
- If write-docs polish is undesired → skip, present raw draft
- Existing tickets in `docs/backlog/` are unaffected; new tickets gain the extra subsection between `## Context` and the next section

No template format breakage.

## Out of scope

- Reorganizing the existing template structure (metadata, AC, environment), only adding a new subsection
- Replacing the tracker push logic, that flow is untouched
- Adding new ticket types, the three existing (Story/Task, Bug, Spike) are sufficient
- Changing the file-naming or INDEX convention
