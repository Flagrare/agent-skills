# agent-skills

Twenty-seven skills that wrap around your development cycle in Claude Code. They turn tickets into ATDD plans, smoke-test features against a running app or service, hunt down bugs with runtime evidence, guard commits against doc drift, run seven-axis code review, draft changelogs that read like patch notes, and review PRs with full context from your tracker and design tools.

All skills are namespaced under `flagrare:*` to avoid collisions with other plugins. Installing this marketplace adds `/flagrare:intake`, `/flagrare:work-prep`, `/flagrare:smoke-test`, `/flagrare:wrap-up`, `/flagrare:pr-reviewer`, and twenty-two more to every Claude Code session.

## Install

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/install.sh)
```

One command. It registers the marketplace, installs the `flagrare` plugin, and makes all twenty-seven skills available. Restart Claude Code or run `/reload-plugins` afterward.

If you prefer to clone first:

```bash
git clone git@github.com:Flagrare/agent-skills.git && ./agent-skills/install.sh
```

### Already installed on an older version?

If you're on a release before `1.3.1`, the cached version of `/flagrare:update` has obsolete logic baked into its text and can't update itself. Run the canonical updater directly from GitHub once, it will heal any stale marketplace, plugin, or settings state:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

After this one-time bootstrap, `/flagrare:update` works for all future versions because it now just calls the same script from main.

## What each skill does

### Planning and context

`/flagrare:intake` reads a ticket (via Jira MCP, Linear, GitHub CLI, or a pasted URL), dispatches parallel subagents to follow every linked doc and PR, and assembles a context brief. Before asking clarifying questions, it grounds the brief in the actual code via `/flagrare:codebase-explore`, so questions reference specific files (`src/x.ts:84`) instead of abstract architecture. Hands off to `/flagrare:atdd-plan`.

`/flagrare:atdd-plan` produces an implementation plan in Claude Code's native plan mode. It enters plan mode via `EnterPlanMode`, runs `/flagrare:codebase-explore` to ground the plan in real files, and produces a plan-mode plan that must include 3-5 behavior-first acceptance tests defining "done" before implementation and any non-trivial structural decisions named as design patterns with a one-line rationale. `ExitPlanMode` closes with the native approve/edit/reject button UI. The skill stops at the plan; it does not write implementation code.

`/flagrare:work-prep` orchestrates the full ticket-to-plan workflow. It calls `/flagrare:intake` first (which now grounds the brief in code before asking codebase-aware clarifying questions), then `/flagrare:atdd-plan` (which runs its own thorough exploration pass and produces an ATDD-first plan). One command from ticket to plan.

`/flagrare:codebase-explore` maps conventions, reusable utilities, analogous features, and data flows for a planned change. Returns raw findings only (no plan, no tests). Used as the codebase grounding step by `/flagrare:intake`, `/flagrare:atdd-plan`, and `/flagrare:ticket-creator`, or standalone when you need to understand a feature area.

`/flagrare:tdd-writer` drafts Technical Design Documents for large projects (2+ weeks). It fetches context from Jira, Confluence, Figma, and Notion via MCP, analyzes the actual codebase, and marks every unverified claim explicitly, nothing is assumed. It writes through `/flagrare:write-docs`, so the result reads as narrative a reviewer can follow start to finish (what's proposed, why, and how) rather than a checklist with the prose removed.

`/flagrare:ticket-creator` writes well-structured tickets as reviewable markdown files, then pushes to any tracker (Jira, Linear, GitHub Issues, Shortcut, Asana, Trello) via MCP or CLI after you review and approve. Before drafting, it calls `/flagrare:codebase-explore` to find specific file paths, conventions, and prior attempts, so the ticket points at `path/to/file.ts:42` instead of gesturing at "the relevant area". For spec/TDD-to-backlog flows it dispatches the explorations in parallel. After drafting, it polishes the Context section via `/flagrare:write-docs` so the prose reads like a senior engineer wrote it, not a template.

### Learning

`/flagrare:tutor` is on-demand Socratic tutoring mode. Claude switches from doing the work to teaching you how to do it, questions instead of answers. You pick scope per call (tutor against current context, against a named topic, or instead of implementing the thing Claude was about to build) and persona in ascending intensity (Echo for calm/observational, Cipher for puzzle-handler, Vex for pushes-hard). Refuses to reveal the answer until you explicitly ask or accept a stuck-offer at three consecutive stalls. Exits only on explicit close phrase ("stop tutoring"), no model-side mastery gate. On first invocation in a repo, asks whether to record per-session summaries to `.flagrare/tutor-log.md` as a learning-path log.

### Quality gates

`/flagrare:smoke-test` validates the feature you just implemented against a running instance. For UI work it drives a browser via Playwright MCP and diagnoses failures with Chrome DevTools MCP; for backend work it hits the running service through the project's existing test framework. Auto-detects domain from the diff (UI, backend, or full-stack). Tests every acceptance criterion plus exploratory edges (long inputs, slow network, auth matrix, idempotency, observability spans, the 403/404 tenant-leak), fixes every gap or bug found, then captures the working trajectory as a permanent Playwright spec or test file before declaring done. Ten-minute budget.

`/flagrare:bug-bash` runs a prescribed test plan against a real running system with evidence at every step. Ingests test cases from Notion (via the Notion MCP), markdown files, PR descriptions, or pasted text. Drives the UI via Chrome DevTools MCP or Playwright MCP; hits backend endpoints via Postman CLI, curl, or HTTP MCPs. Walks every prescribed case (the strict pass), then layers a five-lens exploratory pass: viewports, edge inputs, multi-actor flows in isolated browser contexts, codebase-driven concerns, and extra context the user provides (meeting transcripts, follow-up Slack threads). Lands results in a local markdown audit file by default, then optionally writes back to the source of truth, filling Eng QA columns and adding entries to the linked bug database in the team's own voice. Strict rule throughout: never claims a bug it didn't itself reproduce. Distinct from `/flagrare:smoke-test`, which is narrower and scoped to the feature the author just implemented; bug-bash is wider, longer-running, and often runs against features other people built.

`/flagrare:staleness-audit` diffs your staged changes against the repo's documentation surfaces (README, ADRs, public exports, doc comments, test names, changesets) and flags drift before it lands in history.

`/flagrare:implementation-review` launches seven parallel subagents: plan-gap detection, use-case coverage, missing test scenarios, test philosophy (Kent Dodds Testing Trophy), SOLID violations, Clean Code violations, and security. The security check pulls in `/flagrare:security-audit`.

`/flagrare:security-audit` is the collection's security pass. It reviews the staged diff for HIGH-confidence, concretely exploitable vulnerabilities (injection, broken authn/authz, secrets and data exposure, unsafe deserialization, crypto misuse, SSRF), scoped to the change plus its trust boundary, and audits dependencies with the repo's own package manager when a lockfile moved (degrading to an advisory flag when the auditor is not installed). Every finding carries a concrete exploit path; theoretical noise is dropped. Runs as Check 7 of `/flagrare:implementation-review` and standalone on demand.

`/flagrare:wrap-up` runs automated checks (tests, lint, types), invokes `/flagrare:implementation-review`, then layers additional SOLID and Clean Code review for anything not covered. The combined report tells you whether to commit or fix first.

`/flagrare:release-check` detects the project's release mechanism, decides whether a release is due, and drafts a semver bump with a value-focused changelog entry.

`/flagrare:ux-audit` drives the running app via Chrome DevTools MCP through every reachable route and every visible affordance, screenshots each state, and writes a severity-ranked findings table (`.ux-audit/FINDINGS.md`) with location, why-it's-painful, and recommended fix. Accepts an optional scope ("UX audit the onboarding flow") to restrict to specific routes; defaults to all routes when no scope is given. Pretends to be a first-time user, surfaces jargon, mystery glyphs, dead-end empty states, choice paralysis, color-only signals, jarring tone, mobile-first violations. Goal-locked so it can't exit before coverage is complete. Installs Chrome DevTools MCP automatically if not already available.

`/flagrare:debug-hunt` is evidence-first debugging for bugs that are hard to reproduce, intermittent, or where previous static-analysis fixes have failed. It sets an explicit `/goal` (the bug no longer reproduces), then loops through Hypothesis → Instrument → Reproduce → Analyze → Fix until that goal is met. In Phase 1 it offers to invoke `/flagrare:smoke-test` to surface evidence from a live instance before touching code. When the repo has tests, Phase 4 invokes `/flagrare:atdd-plan` to write a failing acceptance test before the fix, so the bug is captured before it's killed. All instrumentation is tagged `[DEBUG-HUNT]` for clean removal once the fix is verified.

`/flagrare:five-lens-review` spawns five parallel persona subagents, Senior PM, Senior Product Engineer, Senior Product Designer, Senior Design Engineer, and a realistic end user, each examining the same product-direction question through their discipline's lens, then synthesizes convergent themes, disagreements, and a single actionable recommendation. Use when a user-facing decision has multiple competing constraints (lifecycle behaviour, data-model trade-offs, destructive actions, UX choices that touch retention) and a single-perspective answer would silently lock in the wrong default.

### Review

`/flagrare:pr-reviewer` fetches linked Jira tickets, Figma designs, and Notion docs via MCP, spawns five parallel subagents for systematic code review (correctness, security, tests, SOLID, clean code), then drafts friendly, humanized GitHub-ready comments you can paste directly.

`/flagrare:open-pr` creates a pull request that follows the repo's PR template. It reads `.github/PULL_REQUEST_TEMPLATE.md`, fetches linked tickets for context (tracker-agnostic), and fills each section with narrative prose (not file enumerations). Descriptions explain what changed from both a product and code perspective, link relevant tickets, and include specific testing notes.

`/flagrare:daily-code-review` reports on your team's open PRs. It queries GitHub for every open PR across a configured roster, classifies each by staleness (>24h pod-wide, >12h yours-to-touch) and review state, and renders three sections: stale PRs needing action, PRs needing your attention (yours to review or yours to merge), and parked drafts. First run prompts for the GitHub org and team members, then saves the config under the skill for future runs.

`/flagrare:standup-report` writes your daily standup as a Staff Engineer would deliver it, impact-driven, root-cause-aware, and honest about judgment calls. It pulls from GitHub (your PRs, reviews left, comments addressed, merges, deploys), local git across configured repo roots, the project's release automation, and any tracker MCP you've configured (Linear, Jira, Notion, etc.). The output is a short narrative paragraph plus a journal-style recap plus a slack-pasteable bullet list. Names work in human terms, "fixed the image cache eviction" not "PR #481", and resolves "yesterday" as your last working day, so Monday standups cover Friday. On first install, prompts for additional MCPs (Slack, calendar) that can feed narrative context.

`/flagrare:brag-doc` is standup-report's long-arc counterpart. Ask for a day, week, biweek, month, or custom range, and the skill clusters your activity (authored PRs, reviews given, commits, deploys, linked tickets) into 3-6 impact themes, then renders a brag-doc-formatted markdown document, headline, themed sections leading with outcomes, IC contributions separated from amplification, learnings, open threads, refs. The output drops into a dev journal, a personal bragging sheet, or a performance-review packet as-is. Pass `resumancer` as a mode argument (`/flagrare:brag-doc resumancer`) and the skill emits a bash block of ready-to-paste `resumancer` CLI commands instead, with command types (build / impact / reflection / goal) mapped from theme shape.

`/flagrare:senior-scan` scans your org's communication surfaces for openings to operate at the next level, decisions still being formed, people stuck or circling, discussions missing context only you have, cross-team changes touching systems you own. One read-only sweep agent per surface (chat, code review, docs and tickets, chosen at onboarding from the MCPs actually connected) feeds a five-axis score (leverage, credibility, stretch, audience, timing) behind a hard anti-performative filter: no leverage or no credibility kills an item no matter how visible the thread, because shallow drive-bys hurt the promotion case they were meant to build. Output is a max-5 digest with fully contextualized items and draft replies in your own voice (distilled from your real messages at onboarding), gated behind per-message approval. Posted contributions append to an evidence log that `/flagrare:brag-doc` consumes at review season.

### Implementation support

`/flagrare:figma-matcher` enforces pixel-perfect implementation of Figma designs. It extracts every visual property from Figma, spins up Chrome DevTools to measure the current implementation, builds a comparison checklist, and fixes all discrepancies in a single pass.

`/flagrare:interaction-polish` elevates the feel and "juice" of UI interactions, in the craft tradition of Emil Kowalski (sonner, vaul) and Josh Comeau. Point it at a stiff component or describe an interaction, and it applies tasteful motion (easing, springs, micro-feedback, the small details that make an interface feel alive) with accessibility (`prefers-reduced-motion`) and performance (compositor-only properties) built in. CSS-first, adapts to the project's stack. Its defining trait is restraint: it frequency-gates motion, leads with feedback over decoration, and knows when not to animate at all (a command palette summoned a hundred times a day should feel instant, not animated). Distinct from `/flagrare:ux-audit`, which finds usability problems; this one improves how an interaction feels.

`/flagrare:design-review` evaluates and refines a UI the way a senior product designer would, then applies the highest-leverage fixes: visual hierarchy, spacing and rhythm, a real type scale, legibility, information density, and restraint. It diagnoses first (names the screen's one job, runs the squint test, prioritizes findings by leverage), respects and extends the project's existing brand or design system before inventing anything, and grounds every call in the canon (Dieter Rams, Edward Tufte, the Gestalt principles, the Vignelli Canon, Nielsen's heuristics) plus the Refactoring UI playbook. Its instinct is to remove, demote, and quiet before adding. Works on UI code or a screenshot. Distinct from `/flagrare:ux-audit` (a usability walkthrough) and `/flagrare:interaction-polish` (motion and feel); this one is visual, product-design craft.

`/flagrare:research-catalog` fires whenever you do external research (WebFetch, WebSearch, Explore-agent). It catalogs sources under `docs/research/` in the consuming project before returning the synthesis, so decisions trace back to evidence.

`/flagrare:write-docs` guides documentation writing using Pinker's classic style, the Diataxis framework, and concrete examples from React, Stripe, and Anthropic's docs.

`/flagrare:editorial-pass` reviews a finished draft the way a human editor reads it: whole document, start to finish, building a model of what it's trying to communicate before judging a single line. It diagnoses throughline, sequencing, pacing, and consistency from large to small, then hunts three noise categories agents habitually leave behind (provenance narration like "as verified in X", ruled-out-hypothesis residue like "we confirmed it is not Y", and self-referential scaffolding like "resolved since drafting"). It delivers an editorial memo first and only rewrites on approval. Strictly a prose editor, not a technical reviewer: it judges the writing, never the design the writing describes. The read-and-repair counterpart to `/flagrare:write-docs`.

`/flagrare:testing-philosophy` is the shared definition of a good test, distilled from Kent Dodds and generalized to any language and layer (frontend, backend, CLI, library): behavior over implementation details, the Testing Trophy, and a hard floor requiring at least one end-to-end test of the critical happy path for user-facing features. It's the required background for `/flagrare:atdd-plan`, `/flagrare:implementation-review`, and `/flagrare:tdd-writer`.

### Maintenance

`/flagrare:update` pulls the latest skills from GitHub. It runs the canonical `update.sh` from `main` directly, so the update logic is always current even if your locally cached skill is from an older release. It migrates legacy marketplace names, installs the plugin so version refreshes propagate, scrubs stale settings entries, and prunes obsolete caches in a single run.

`/flagrare:uninstall` removes the flagrare plugin and marketplace registration. Run it to cleanly disable all skills.

## Workflow

A typical feature cycle:

```
/flagrare:work-prep [ticket]     you have a ticket, need context + plan
  /flagrare:intake                 (context gathering, called by work-prep)
    /flagrare:codebase-explore       (ground brief in code, then ask codebase-aware questions)
  /flagrare:atdd-plan              (codebase exploration + plan, called by work-prep)
    /flagrare:codebase-explore       (atdd-plan's own pass, stays self-sufficient for standalone use)
[implementation]                 you have a plan, write code
/flagrare:figma-matcher          UI work done, verify against Figma
/flagrare:smoke-test             feature done, validate behaviour against a running app or service
/flagrare:wrap-up                code done, full quality gate
  /flagrare:implementation-review  (seven-axis review, called by wrap-up)
/flagrare:staleness-audit        docs didn't drift
git commit                       everything passes, commit
/flagrare:open-pr                push and open a PR with proper context
/flagrare:release-check          committed, decide if a release ships
```

`/flagrare:research-catalog` slots in wherever external research happens. `/flagrare:pr-reviewer` runs when reviewing someone else's PR. `/flagrare:open-pr` runs when you're ready to push and get reviewed. `/flagrare:tdd-writer` and `/flagrare:ticket-creator` run during planning phases for larger projects. `/flagrare:update` refreshes skills from GitHub; `/flagrare:uninstall` removes everything cleanly.

## Developing skills locally

If you want to edit these skills and see changes without pushing to GitHub:

```bash
git clone git@github.com:Flagrare/agent-skills.git ~/Dev/agent-skills
claude plugin marketplace remove flagrare-skills
claude plugin marketplace add ~/Dev/agent-skills
```

After this, edits in `~/Dev/agent-skills` take effect on `/reload-plugins`. To switch back to the published version, reverse the process: remove and re-add with the GitHub path.

## Troubleshooting

Run `/doctor`. It names the specific plugin and the specific failure.

For most issues, run the canonical heal script, it fixes stale marketplace names, half-installed plugins, missing settings entries, and obsolete caches in one pass:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

| Symptom | Fix |
|---|---|
| `N errors during load` | Run `/doctor` for the exact plugin and error |
| `Plugin X not found in marketplace flagrare-skills` | Run the heal script above |
| Slash commands missing, 0 errors | Run the heal script above, most often the plugin is enabled but not installed |
| Marketplace operation hangs | Run the heal script above, it cleans the marketplace and re-clones from GitHub |
| `/flagrare:update` runs old logic | You're on a pre-1.3 cached skill. Run the heal script above once; future `/flagrare:update` calls work correctly |
