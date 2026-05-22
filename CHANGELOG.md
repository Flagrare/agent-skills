# Changelog

## 1.5.1 — 2026-05-22

The work-prep flow no longer ends mid-conversation when a tool-driven prompt would close the loop. Every gate now uses interactive button-prompts — the same UX as plan-mode's accept tool — instead of prose questions the model would narrate and then stop on.

### Bug Fixes

- **`/flagrare:intake`** clarifying questions: now batched into a single `AskUserQuestion` tool call with concrete options per question. Previously the skill narrated questions as prose and the turn ended without your answer being captured.
- **`/flagrare:intake`** standalone completion: ends with a tool-driven next-step prompt — **Proceed to /flagrare:atdd-plan (Recommended)** or **Stop here**. Was: silent context dump with no prompt.
- **`/flagrare:intake`** next-step options pruned: dropped `/flagrare:ticket-creator` and `/flagrare:tdd-writer` from the prompt — those run earlier in different workflows (decomposing specs into tickets, drafting design docs for new multi-week projects), not downstream of a single-ticket intake.
- **`/flagrare:work-prep`** post-plan confirmation: ends with a tool-driven prompt — **Start implementation (Recommended)** / **Adjust the plan** / **Stop here**. Was: prose "say 'go' to start" which let the turn end ambiguously.

## 1.5.0 — 2026-05-22

`/flagrare:intake` now knows what's already in the codebase before asking you anything. Clarifying questions reference specific files instead of asking abstract architectural questions.

### Behaviour

- **`/flagrare:intake`**: between brief synthesis and clarifying questions, runs `/flagrare:codebase-explore` to populate a new `## Codebase Findings` section in the brief. The 3–5 questions asked next are now codebase-aware: *"I see `src/billing/quote.ts:84` already handles the discount math — extend it or fork it?"* instead of *"where should the discount logic live?"*. Skips exploration for pre-code projects, docs-only repos, process-only tickets, or when the user asks for a "rough intake".
- **`/flagrare:atdd-plan`**: unchanged. Still always runs its own `/flagrare:codebase-explore` pass — intake's findings in the brief are additive input, not a substitute. Keeps atdd-plan self-sufficient when invoked standalone (without going through intake or work-prep).
- **`/flagrare:work-prep`**: orchestration documentation updated to reflect the new intake order and the deliberate double-exploration design (once in intake to inform questions, once in atdd-plan to anchor the plan).

### Documentation

- **README**: intake, work-prep, and codebase-explore descriptions catch up with the new flow; workflow diagram shows intake's grounding step.

## 1.4.0 — 2026-05-22

`/flagrare:ticket-creator` now points at the actual code. Engineers picking up tickets no longer have to re-do the codebase exploration the skill could have done once at draft time.

### Behaviour

- **`/flagrare:ticket-creator`**: before drafting, calls `/flagrare:codebase-explore` to find specific file paths, conventions, and prior attempts. The resulting findings appear in a new optional subsection — `Suspect Code` for bugs, `Existing Patterns` for features, `Prior Work` for spikes — populated with `path/to/file.ts:42`-style references instead of vague gestures at "the relevant area".
- **`/flagrare:ticket-creator`**: after drafting, polishes the Context section via `/flagrare:write-docs`. The Context reads like a senior engineer wrote it after reading the code, not a template filled in from requirements. Mechanical sections (acceptance criteria, environment, metadata) stay untouched.
- **Spec/TDD → backlog flows**: codebase exploration runs in parallel (one `Agent` call per candidate ticket emitted in a single message), so N tickets take roughly the same wall-clock as 1.

### Skip conditions

The new orchestration steps are conditional. Both auto-skip when:
- The current directory isn't a git repo or contains no source files (pre-code projects, docs-only)
- The user asks for a "rough draft" or "skip exploration"
- The ticket is purely process (e.g. `[INFRA] rotate keys`) where exploration adds no value

### Design

- **No external skill dependencies.** flagrare skills are self-contained. The parallel dispatch uses `Agent` tool calls directly, not a wrapping skill from another plugin.

## 1.3.1 — 2026-05-22

Fixes the self-migration flow that 1.3.0 promised but didn't fully deliver. The `/flagrare:update` skill now heals any prior state in one run.

### Behaviour

- **`/flagrare:update`**: the skill body is now a curl-shim that fetches the canonical `update.sh` from `main`. Stale skill text can no longer trap users on obsolete update logic.
- **`update.sh`**: uses `claude plugin install` (registers the plugin so `claude plugin update` can pull new versions) rather than `claude plugin enable` alone. Adds an explicit `claude plugin update` step. Scrubs stale `flagrare@<old>` settings entries unconditionally, even when the legacy marketplace was already removed manually. Prunes legacy `~/.claude/plugins/cache/<old-name>` directories.

### Documentation

- **Troubleshooting**: now leads with the heal script. The old advice to remove and re-add the marketplace manually left users in the `enable`-without-`install` half-state that 1.3.1 fixes.
- **`/flagrare:update` description**: previously claimed it just refreshed the marketplace cache. Updated to describe the full self-healing flow.
- **`install.sh`**: was missing `/flagrare:codebase-explore` from its skill list output.

## 1.3.0 — 2026-05-22

Plugin installs and updates now self-migrate from older marketplace names. Users on previous versions can run `/flagrare:update` once to land on the new identifier without manual cleanup.

### General

- **Marketplace name**: `personal` → `flagrare-skills`. The name `personal` implied an installer's own collection; the new name describes what the marketplace actually is.

### Behaviour

- **`/flagrare:update`**: detects an existing `personal` marketplace, disables `flagrare@personal`, removes the marketplace, scrubs the stale `enabledPlugins` entry, then re-adds under the new name. No-op when already on `flagrare-skills`.
- **`install.sh` and `update.sh`**: share one migration block via `update.sh` — single source of truth, install delegates to it.

### Bug Fixes

- Migration detection now matches by marketplace name rather than source URL. Previously, local-path installs (e.g. `claude plugin marketplace add ~/Dev/agent-skills`) silently skipped migration because their source string didn't match `Flagrare/agent-skills`.

## 1.2.0 and earlier

Pre-changelog. See `git log` for history.
