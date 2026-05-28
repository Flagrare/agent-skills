# Changelog

## 1.14.0 — 2026-05-28

`/flagrare:tutor` is a new Socratic tutoring mode that switches Claude from doing the work to teaching the user how to do it, via questions instead of answers. User picks scope and persona per call. Closes only on explicit phrase. Optional per-repo learning-path log.

### Behaviour

- **`/flagrare:tutor` — three scope modes**: in-context (against current file/PR/function/error), topic (user names what to learn), or instead-of-implementing (Claude was about to build something; user opts to learn how to build it instead and writes the code themselves).
- **`/flagrare:tutor` — three personas, ascending intensity**: Echo (calm, observational), Cipher (knowing, puzzle-handler), Vex (pushy, leading). Persona affects voice only — same Socratic engine underneath.
- **`/flagrare:tutor` — Socratic guardrails**: refuses to reveal the answer unless the user explicitly asks. Stuck-detection at three consecutive stalls offers a sharper-hint, show-me, or keep-going escape. Reveal mode has a 3-rung scaffolding ladder ending in a local verify-back question.
- **`/flagrare:tutor` — explicit-phrase close only**: exits on "stop tutoring", "end tutor", "exit tutor mode", or similar. No model-side mastery gate.
- **`/flagrare:tutor` — per-repo learning-path log (opt-in)**: on first invocation in a project directory, asks whether to record per-session summaries to `.flagrare/tutor-log.md`. Opt-out is per-repo and silent on subsequent calls. Non-project directories skip logging entirely.
- **`/flagrare:tutor` — explicit-trigger only**: fires only on phrases like "tutor me on X", "tutor mode", "be my tutor", "Socratic me", or "/flagrare:tutor". Does NOT auto-trigger on colloquial "teach me X" or "explain this" — those usually mean the user wants a quick answer.

## 1.13.6 — 2026-05-28

`/flagrare:work-prep` now reliably hands off to `/flagrare:atdd-plan` after intake completes its full workflow.

### Bug Fixes

- **`/flagrare:work-prep` → `/flagrare:atdd-plan` handoff**: the PostToolUse hook fired when intake's SKILL.md loaded (before the model read it), not when intake's multi-step workflow finished — so the model received contradictory "do intake steps 0–6" and "skip to atdd-plan NOW" directives simultaneously. Replaced hook-based chaining with a `[work-prep]` prefix convention: intake detects the prefix at Step 6 completion and invokes atdd-plan itself.

## 1.13.5 — 2026-05-28

`/flagrare:standup-report` Today section now includes pending review requests — open PRs where a teammate explicitly requested the user's review and no review has been submitted yet.

### Behaviour

- **`/flagrare:standup-report` — Today: pending reviews**: a new second tier between carry-overs and the priority queue. Fetches open, non-draft PRs where `review-requested:{LOGIN}` is set and the user hasn't submitted a review yet. Ordered by `updated_at` descending (most recently active first). Each entry names the author ("Daniel's auth service changes") so the user knows who's waiting. Excluded: PRs already reviewed in the window, draft PRs, PRs authored by the user.
- **`/flagrare:standup-report` — Today ordering**: carry-overs → pending review requests → priority queue. Review requests sit between the two because they're explicit external asks — someone is blocked — but carry-overs (work already in motion) take precedence.
- **`/flagrare:standup-report` — For the channel Today block**: example updated to show all three tiers in compact form.

## 1.13.4 — 2026-05-28

`/flagrare:standup-report` now generates a two-part report: a Yesterday section covering the last working day, and a Today section that infers what's likely on deck — carry-over threads first (open PRs, draft PRs, local branches not yet PR'd), then priority-ordered assigned tickets from the configured tracker.

### Behaviour

- **`/flagrare:standup-report` — Today section**: new section between Recap and For the channel. Carry-overs (open/draft PRs and unpushed branches still in motion) appear first, ordered by proximity to merge. Assigned tracker tickets in To Do / Backlog / Unstarted state follow, ordered by priority (Urgent → High → Medium → Low → No priority). Items shared between carry-overs and the queue are deduplicated — the carry-over entry wins. Section is omitted entirely when both lists are empty.
- **`/flagrare:standup-report` — For the channel Today block**: the channel section now has a Yesterday sub-block (yesterday bullets unchanged) and a Today sub-block (1-3 lines, hedged as "likely", "continuing", "starting on"). Cap of 3 items — the team needs the headline, not the full queue.
- **`/flagrare:standup-report` — data collection step 8**: new parallel query collects carry-overs from already-fetched GitHub data (no extra API calls for carry-overs) and fetches assigned To Do tickets from the configured tracker MCP.

## 1.13.3 — 2026-05-28

`/flagrare:debug-hunt` gains a Pattern Analysis phase before instrumentation: if a working implementation of the same pattern exists elsewhere in the codebase, a side-by-side diff often reveals the root cause without writing a single log line.

### Behaviour

- **`/flagrare:debug-hunt` — Phase 2 (Pattern Analysis)**: new phase inserted between Context & Hypotheses and Instrumentation. Searches for working implementations of the same pattern elsewhere in the codebase, then diffs working vs. broken. If the diff is conclusive, the skill skips directly to Resolution (Phase 5) — no instrumentation needed. If inconclusive, it proceeds to Instrumentation (Phase 3) carrying any hypotheses the comparison generated. All subsequent phases renumbered.

## 1.13.2 — 2026-05-28

`/flagrare:standup-report` no longer surfaces skill invocations or process steps in its output, and the "For the channel" section now opens with a big-picture line before the bullets.

### Behaviour

- **`/flagrare:standup-report` — channel section**: opens with a one-sentence big-picture framing of the day before the bullet list, so the reader gets the theme before the detail.
- **`/flagrare:standup-report` — output filtering**: skill invocations, slash commands, AI tooling used, and pure process steps (`ran debug-hunt`, `grepped the codebase`, `ran evals`) are now explicitly excluded from all output sections. Engineering outcomes are reported; the methods used to reach them are not.

## 1.13.1 — 2026-05-28

Renamed `/flagrare:debug` → `/flagrare:debug-hunt` to avoid collision with Claude Code's built-in `/debug` command.

### Behaviour

- **`/flagrare:debug-hunt`**: same skill, new name. `/debug` is a built-in Claude Code command; `/flagrare:debug-hunt` is now the unambiguous way to invoke the evidence-first debugging workflow.

### Documentation

- **README**: Quality gates entry updated to `/flagrare:debug-hunt`.
- **CHANGELOG**: 1.13.0 entry updated to reflect the canonical skill name.

## 1.13.0 — 2026-05-28

A new skill, `/flagrare:debug-hunt`, brings evidence-first debugging into the flagrare workflow. It ports the "Evidence Over Speculation" philosophy from runtime-oriented debugging agents into Claude Code, enforcing a scientific loop that doesn't let you commit to a fix until runtime data confirms the root cause.

### Behaviour

- **`/flagrare:debug-hunt`**: sets an explicit `/goal` at the start (the bug no longer reproduces, root cause confirmed by evidence, all instrumentation removed, codebase clean) and works until every condition holds. Phase 1 offers to invoke `/flagrare:smoke-test` to explore the bug against a live instance before reading any code — useful for UI glitches, wrong API responses, and timing issues that are invisible in static analysis. Phase 2 adds surgical, tagged instrumentation (`[DEBUG-HUNT]` prefix) so cleanup is a grep, not a memory exercise. Phase 3 waits for real log output before proceeding — no guessing from code shape. Phase 4 conditionally invokes `/flagrare:atdd-plan` when the codebase has tests: the fix must be preceded by a failing acceptance test that captures the bug in its pre-fix state, making the regression proof permanent. Phase 5 verifies the fix with instrumentation still in place (so a partial fix doesn't hide under removed logs), then removes all `[DEBUG-HUNT]` lines and confirms the test suite is clean.

### Documentation

- **README**: new entry under the Quality gates section; skill count bumped from twenty-three to twenty-four in the header, install line, and intro paragraph.

## 1.12.2 — 2026-05-26

`/flagrare:standup-report` no longer guesses what day of the week it is.

### Bug Fixes

- **`/flagrare:standup-report` time window**: the skill now runs `date '+%A %Y-%m-%d %H:%M'` explicitly instead of inferring the weekday from the date string. Previously, a wrong inference meant the entire report covered the wrong day's activity.
- **Same-day work captured**: the window now extends through the current time (not midnight of the previous day), so commits and PRs landed earlier today appear in the standup.

## 1.12.1 — 2026-05-26

`/flagrare:atdd-plan` now produces an actual plan-mode plan instead of a wall of enumerated sections. The old form filled in eight forced subsections (SOLID audit, Clean Code checklist, gap-review-by-category, design-patterns table, implementation-phases table, refactor reminder, etc.) and ended without interaction; modern Claude filled every subsection exhaustively, producing 500+ word plans with no approve/edit/reject UX. The skill now delegates the plan's shape to Claude Code's native plan mode.

### Behaviour

- **`/flagrare:atdd-plan`**: enters plan mode via `EnterPlanMode` at skill start, runs `/flagrare:codebase-explore` to ground the plan in real files, posts a 3-5 sentence synthesis with an `AskUserQuestion` confirmation gate (one button click in the common case), produces a plan-mode plan, and closes with `ExitPlanMode` so the user gets the native approve/edit/reject button UI. Two inclusions are enforced on top of plan mode's default shape: 3-5 ATDD acceptance tests (behavior-first, public-API-only, Testing Trophy shape) and named design patterns with one-line rationale (or explicitly "none needed" when no non-trivial structural decisions exist).
- **Removed from the output** so the model can't fall back into them: SOLID audit, Clean Code checklist, gap review enumerated by seven categories, Design Patterns table, Implementation Phases table, Refactor Pass Reminder. Specific risks anchored in what exploration found stay — listed inline in the prose, not as a separate forced section.

### Documentation

- **README**: `/flagrare:atdd-plan` entry rewritten to drop the no-longer-true "SOLID audit / gap review / structured plan" framing; replaced with the plan-mode + ATDD + named-patterns framing matching the new skill.

## 1.12.0 — 2026-05-26

A new skill, `/flagrare:brag-doc`, generates a long-arc, impact-framed retrospective for any time window you pick. It's the journaling and self-review counterpart to `/flagrare:standup-report` — same data sources, inverted output: themed by impact instead of chronological, accomplishment-framed instead of conversational, durable instead of ephemeral.

### Behaviour

- **`/flagrare:brag-doc`**: asks for a window (today, this week, last week, last 2 weeks, this month, last month, or any free-form range like "since 2026-05-01"), collects authored PRs, reviews given, comments, commits, deploys, and linked tickets across GitHub, local git, release automation, and tracker/extra MCPs. Clusters the activity into 3-6 impact themes (not per-PR bullets) and renders a brag-doc-formatted markdown document — headline, themed shipped work leading with outcomes, IC contributions separated from amplification, learnings, open threads, refs. The synthesis enforces a Staff-Engineer voice (lead with what got better and by how much; quantify; own in first-person active voice; name judgment, not just shipping) with a before/after example showing the same five events as bland enumeration vs brag-doc voice.
- **`/flagrare:brag-doc resumancer`**: same synthesis pipeline, different render. Emits a bash code block of ready-to-paste `resumancer` CLI commands (`resumancer impact "..." --branch ... --commit ... --public`), one per theme/unblock/reflection, with command type mapped from theme shape (quantified outcomes → `impact`, shipped capability → `build`, learning → `reflection`, open thread → `goal`).

### Documentation

- **README**: new entry under the Review section; skill count bumped from twenty-two to twenty-three in the header, install line, and intro paragraph.

## 1.11.1 — 2026-05-26

`/flagrare:release-check` now insists on annotated tags so `git push --follow-tags` actually pushes them. Lightweight tags (the default for `git tag <name> <sha>` with no `-a`) are silently skipped by `--follow-tags`, which means the tag sits on your machine while the rest of the release looks green. v1.10.0 of this plugin hit exactly that — the lesson now lives in the skill.

### Behaviour

- **`/flagrare:release-check`**: action plan now prescribes `git tag -a vX.Y.Z -m "release vX.Y.Z" <sha>` instead of the lightweight form, and adds `git ls-remote --tags origin | grep vX.Y.Z` as a post-push verification so a silent-skip can't slip past. The anti-patterns list gains an entry explaining why lightweight tags are the trap, so the lesson is searchable from the failure-mode angle too.

## 1.11.0 — 2026-05-26

A new skill, `/flagrare:standup-report`, writes your daily standup the way a Staff Engineer would deliver it — impact first, root cause named, judgment calls owned. No more verb-first task lists pretending to be a recap.

### Behaviour

- **`/flagrare:standup-report`**: pulls your authored PRs, reviews given, comments addressed, merges, deploys, and linked tickets across GitHub, local git (configured repo roots), the project's release automation, and any tracker MCP (Linear, Jira, Notion, Asana, Shortcut, Trello). On first install, also asks which additional MCPs to feed narrative context (Slack DMs, calendar). Names work in human terms — *fixed the image cache eviction*, not *merged PR #481* — and resolves "yesterday" as your last working day, so Monday standups cover Friday. Output is a 2-3 sentence impact paragraph, a journal-style recap grouped by thread (not by source), a slack-pasteable bullet list, and a refs footnote with the actual identifiers.
- **Synthesis voice**: the skill includes an explicit before/after example showing the junior-recap-as-todo-list vs the staff-recap-as-system-status framings. Bullets carry impact even when compressed ("Pushed back on Carol's cache-benchmark methodology — workload doesn't match prod"), not the naked "Approved X" / "Reviewed Y" cadence.

### Documentation

- **README**: new entry under the Review section; skill count bumped from twenty-one to twenty-two in the header, install line, and intro paragraph.

## 1.10.0 — 2026-05-26

A new skill, `/flagrare:daily-code-review`, reports on your team's open pull requests so you know what to look at before you open GitHub.

### Behaviour

- **`/flagrare:daily-code-review`**: queries GitHub for every open PR across a configured team roster, classifies each by staleness (>24h pod-wide, >12h yours-to-touch) and review state, and renders three sections — stale PRs needing action, items needing your attention (yours to review or yours to merge), and parked drafts. First run prompts for the GitHub org and team members; subsequent runs reuse the saved config under the skill directory. Triggers on phrases like "what should I review", "daily PR check", "show me stale PRs", or a saved pod name.

### Documentation

- **README**: new entry under the Review section; skill count bumped from twenty to twenty-one in the header, install line, and intro paragraph.

## 1.9.3 — 2026-05-25

`/flagrare:ux-audit` is now fully autonomous. It launches Chrome with remote debugging, starts the dev server, and begins route enumeration in parallel -- never stops to ask the user for setup help.

### Behaviour

- **`/flagrare:ux-audit`**: launches Chrome with `--remote-debugging-port=9222` itself (kills existing Chrome first if needed). No longer asks the user to run commands in their terminal.
- **`/flagrare:ux-audit`**: starts the dev server itself (`npm run dev` / `pnpm dev`) if not already running, instead of asking the user to do it.
- **`/flagrare:ux-audit`**: begins route enumeration (Step 2) in parallel while waiting for MCP reconnection, so no time is wasted blocking.

## 1.9.2 — 2026-05-25

`/flagrare:ux-audit` no longer stalls when Chrome DevTools MCP isn't immediately available. The prerequisite section now walks through a structured A/B/C troubleshooting checklist with exact commands, so the model resolves the issue itself instead of asking the user what to do.

### Behaviour

- **`/flagrare:ux-audit`**: prerequisite check is now a structured checklist. Step A: install the plugin (multiple fallback methods). Step B: connect to Chrome (exact `--remote-debugging-port=9222` command for macOS and Linux). Step C: full restart if needed. Models work through all three before stopping.

## 1.9.1 — 2026-05-25

The UX audit now installs its own tooling and keeps the browser visible throughout.

### Behaviour

- **`/flagrare:ux-audit`**: installs `chrome-devtools-mcp` automatically if the tools are missing. No longer asks the user for permission or offers alternatives -- just installs, verifies, and continues.
- **`/flagrare:ux-audit`**: opens a dedicated tab, brings the Chrome window to front on every navigation, and confirms with the user they can see it before proceeding. The user watches the audit happen in real time.

### Documentation

- **README**: ux-audit description updated to mention scope support and auto-install.
- **Skill frontmatter**: description field updated to match.

## 1.9.0 — 2026-05-25

`/flagrare:ux-audit` now accepts a scope. Say "UX audit the onboarding flow" and only those routes are walked; omit the scope and the full app is audited as before. The skill also stops pretending the browser requirement and `/goal` are optional -- both are now hard gates that prevent the executing model from shortcutting.

### Behaviour

- **`/flagrare:ux-audit`**: the executing model now calls `/goal` itself as its first action. Previous wording suggested the user do it; models read that as optional and skipped it every time.
- **`/flagrare:ux-audit`**: Chrome DevTools MCP is a hard prerequisite. If unavailable, the skill stops and asks the user to enable it instead of silently falling back to code-level analysis. Playwright MCP remains an acceptable fallback; static analysis is explicitly prohibited.
- **`/flagrare:ux-audit`**: supports scoped audits. Pass a scope ("audit /settings and /profile") and only those routes are walked; the `/goal` text and Todo list adapt to the specified scope. No scope → all routes (unchanged default).

## 1.8.3 — 2026-05-25

Skills now explain *why* their tool choices are requirements vs. suggestions, so the executing model stops shortcutting past them.

### Behaviour

- **`/flagrare:intake` Step 2**: direct MCP call is now the documented preferred path when the tool is available in-session. Subagent path remains as fallback for large responses or unavailable MCPs.
- **`/flagrare:intake` Step 4.5 + `/flagrare:atdd-plan` Step 1**: carry a "hard requirement" callout explaining why `/flagrare:codebase-explore` must not be substituted with a generic Explore agent -- the skill encodes a specific methodology and structured output that downstream steps depend on.

### Documentation

- **README**: skill count `eighteen → twenty`, `thirteen more → fifteen more`.

## 1.8.2 — 2026-05-25

`/flagrare:update` no longer crashes when the local marketplace cache directory can't be renamed. The script now self-heals: removes the stale directory and re-adds from scratch.

### Bug Fixes

- **`update.sh`**: `marketplace update` failures (EPERM, stale locks) are caught and recovered from automatically instead of aborting the script.

## 1.8.1 — 2026-05-25

Parallel subagents now run on Sonnet instead of inheriting the parent model. Same review coverage, materially lower token cost per invocation.

### Behaviour

- **`/flagrare:implementation-review`**: six parallel check agents now spawn with `model: "sonnet"`.
- **`/flagrare:pr-reviewer`**: five review subagents now spawn with `model: "sonnet"`.
- **`/flagrare:five-lens-review`**: five persona subagents now spawn with `model: "sonnet"`.
- **`/flagrare:intake`**: Ticket Reader and Reference Reader subagents now spawn with `model: "sonnet"`.
- **`/flagrare:ticket-creator`**: parallel codebase-explore agents now spawn with `model: "sonnet"`.

## 1.8.0 — 2026-05-24

Two new skills land together: one audits the user's app like a first-time user would; the other interrogates a product decision through five expert lenses before you commit to it.

### New

- **`/flagrare:ux-audit`**: drives the running app through every reachable route and every visible affordance via Chrome DevTools MCP, screenshots each state, and ships a severity-ranked findings table at `.ux-audit/FINDINGS.md` with location, why-it's-painful, and a one-line recommended fix. Pretends to be a first-time user — surfaces jargon the team has stopped noticing, mystery glyphs in the nav, dead-end empty states, choice paralysis on dense screens, color-only status signals, tone mismatches between affirming and operational copy, mobile-first violations (Drawer-vs-Dialog, sub-44pt tap targets), and premature alarms fired against fresh entities. Goal-locked via the harness's durable-goal mechanism so it can't exit before coverage is complete. Auto-detects route layouts for SvelteKit, Next.js (App + Pages), Nuxt, Rails, and Django; falls back to asking when the framework isn't recognised. Output is one markdown file + numbered screenshots — drop straight into Slack / Notion / PR review.

- **`/flagrare:five-lens-review`**: spawns five parallel persona subagents — Senior PM, Senior Product Engineer, Senior Product Designer, Senior Design Engineer, and a realistic end user — each examining the same product-direction question through their discipline's lens, then synthesises convergent themes, surfaces disagreements, and produces a single actionable recommendation. Use whenever a user-facing decision has multiple competing constraints (lifecycle behaviour, data-model trade-offs, destructive actions, UX choices that touch retention) and a single-perspective answer would silently lock in the wrong default. Especially valuable mid-implementation when an edge case the spec didn't cover surfaces — that's the exact moment one-perspective reasoning ships the wrong choice. (Skill shipped in 1.7.x but was never wired into README or `install.sh`; from this release it's actually reachable.)

### Documentation

- **README**: skill count `eighteen → twenty`. `/flagrare:ux-audit` added under Quality Gates; `/flagrare:five-lens-review` added under Quality Gates (catching up its 1.7.x debut).
- **`install.sh`**: now echoes `/flagrare:ux-audit` and `/flagrare:five-lens-review` so the post-install summary tells users about every skill they actually got.

## 1.7.1 — 2026-05-23

`/flagrare:atdd-plan` now closes with a button-prompt instead of a prose "want me to start?" question — same UX contract intake and work-prep already follow. The turn no longer ends ambiguously after the plan is presented. Also catches up `install.sh` and the README skill count to what shipped in 1.7.0.

### Bug Fixes

- **`/flagrare:atdd-plan`** hand-off: adds Step 9 — after the plan is printed, issues an `AskUserQuestion` call with **Start implementation (Recommended)** / **Adjust the plan** / **Stop here**. Was: prose "Want me to start executing Phase 0, or hold for review?" which let the turn end with no answer captured. Anti-patterns now refuse the prose close explicitly.

### Documentation

- **`install.sh`**: now lists `/flagrare:smoke-test` (new in 1.7.0) and `/flagrare:open-pr` (carried over from 1.6.0). Previously these were installed but not echoed.
- **README**: skill count corrected (seventeen → eighteen) to match the eighteen skill directories.

## 1.7.0 — 2026-05-23

New skill: `/flagrare:smoke-test`. Validates the feature you just implemented against a running instance — UI, backend, or both. Tests every acceptance criterion plus exploratory edges, fixes every gap or bug found, then captures the working trajectory as a permanent test before declaring done.

### New

- **`/flagrare:smoke-test`**: goal-driven validation pass. Auto-detects domain (UI / backend / full-stack) from the diff. For UI, drives the browser via Playwright MCP (semantic accessibility-tree selectors only) and uses Chrome DevTools MCP for failure diagnosis. For backend, hits the running service through the project's existing test framework. Priority-ordered loop: P0 preconditions → P1 acceptance criteria → P2 cross-cutting (console / network / a11y / keyboard / focus on UI; contract / auth-matrix / error-shape / boundaries / idempotency / observability on backend) → P3 exploratory. Fix-and-retest loop until every scenario passes. Captures successful trajectory as a permanent Playwright spec (UI) or test file (backend) — every smoke pass either reveals a bug or leaves a regression test behind, never a throwaway run. Bakes in 2026 best practices including the `403 vs 404` tenant-leak check, observability-driven testing assertions, `retries: 0` policy (flake is a defect), and an under-ten-minute budget.

### Documentation

- **README**: skill count updated (seventeen to eighteen), `/flagrare:smoke-test` description added to Quality Gates, workflow diagram now shows the smoke-test step between figma-matcher and wrap-up.
- **Research catalogs**: `docs/research/2026-05-23-ui-smoke-test-best-practices.md` and `docs/research/2026-05-23-backend-smoke-test-best-practices.md` — the sourced findings the skill is built on (Playwright + Chrome DevTools MCP split, axe + keyboard walk, observability-driven testing, RFC 9457 Problem Details, JWT algorithm-confusion checks).

## 1.6.1 — 2026-05-22

`/flagrare:release-check` now creates a GitHub Release after tagging. Previously the skill stopped at pushing the tag, leaving the Releases page empty and `on: release` workflows untriggered.

### Behaviour

- **`/flagrare:release-check`**: adds `gh release create` as an explicit step between pushing tags and verifying publish workflows. The action plan, execution checklist, and anti-patterns all reflect this.

## 1.6.0 — 2026-05-22

New skill: `/flagrare:open-pr`. Creates pull requests that follow the repo's PR template with contextualized descriptions instead of file-by-file enumerations.

### New

- **`/flagrare:open-pr`**: reads `.github/PULL_REQUEST_TEMPLATE.md`, fetches linked tickets via any available MCP/CLI (tracker-agnostic), and fills the template with narrative prose. Descriptions explain what changed from both a product and code perspective, testing notes are specific, and checklist items are checked appropriately. Sits between `/flagrare:wrap-up` and `/flagrare:release-check` in the workflow.

### Documentation

- **README**: skill count updated (sixteen to seventeen), open-pr description added to the Review section, workflow diagram updated.

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
