# agent-skills

Eighteen skills that wrap around your development cycle in Claude Code. They turn tickets into ATDD plans, smoke-test features against a running app or service, guard commits against doc drift, run six-axis code review, draft changelogs that read like patch notes, and review PRs with full context from your tracker and design tools.

All skills are namespaced under `flagrare:*` to avoid collisions with other plugins. Installing this marketplace adds `/flagrare:intake`, `/flagrare:work-prep`, `/flagrare:smoke-test`, `/flagrare:wrap-up`, `/flagrare:pr-reviewer`, and thirteen more to every Claude Code session.

## Install

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/install.sh)
```

One command. It registers the marketplace, installs the `flagrare` plugin, and makes all eighteen skills available. Restart Claude Code or run `/reload-plugins` afterward.

If you prefer to clone first:

```bash
git clone git@github.com:Flagrare/agent-skills.git && ./agent-skills/install.sh
```

### Already installed on an older version?

If you're on a release before `1.3.1`, the cached version of `/flagrare:update` has obsolete logic baked into its text and can't update itself. Run the canonical updater directly from GitHub once — it will heal any stale marketplace, plugin, or settings state:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

After this one-time bootstrap, `/flagrare:update` works for all future versions because it now just calls the same script from main.

## What each skill does

### Planning and context

`/flagrare:intake` reads a ticket (via Jira MCP, Linear, GitHub CLI, or a pasted URL), dispatches parallel subagents to follow every linked doc and PR, and assembles a context brief. Before asking clarifying questions, it grounds the brief in the actual code via `/flagrare:codebase-explore` — so questions reference specific files (`src/x.ts:84`) instead of abstract architecture. Hands off to `/flagrare:atdd-plan`.

`/flagrare:atdd-plan` produces an implementation plan rooted in acceptance tests. It invokes `/flagrare:codebase-explore` for codebase understanding, names design patterns, runs a SOLID audit, identifies gaps, and outputs a structured plan.

`/flagrare:work-prep` orchestrates the full ticket-to-plan workflow. It calls `/flagrare:intake` first (which now grounds the brief in code before asking codebase-aware clarifying questions), then `/flagrare:atdd-plan` (which runs its own thorough exploration pass and produces an ATDD-first plan). One command from ticket to plan.

`/flagrare:codebase-explore` maps conventions, reusable utilities, analogous features, and data flows for a planned change. Returns raw findings only (no plan, no tests). Used as the codebase grounding step by `/flagrare:intake`, `/flagrare:atdd-plan`, and `/flagrare:ticket-creator`, or standalone when you need to understand a feature area.

`/flagrare:tdd-writer` drafts Technical Design Documents for large projects (2+ weeks). It fetches context from Jira, Confluence, Figma, and Notion via MCP, analyzes the actual codebase, and marks every unverified claim explicitly. Nothing is assumed.

`/flagrare:ticket-creator` writes well-structured tickets as reviewable markdown files, then pushes to any tracker (Jira, Linear, GitHub Issues, Shortcut, Asana, Trello) via MCP or CLI after you review and approve. Before drafting, it calls `/flagrare:codebase-explore` to find specific file paths, conventions, and prior attempts — so the ticket points at `path/to/file.ts:42` instead of gesturing at "the relevant area". For spec/TDD-to-backlog flows it dispatches the explorations in parallel. After drafting, it polishes the Context section via `/flagrare:write-docs` so the prose reads like a senior engineer wrote it, not a template.

### Quality gates

`/flagrare:smoke-test` validates the feature you just implemented against a running instance. For UI work it drives a browser via Playwright MCP and diagnoses failures with Chrome DevTools MCP; for backend work it hits the running service through the project's existing test framework. Auto-detects domain from the diff (UI, backend, or full-stack). Tests every acceptance criterion plus exploratory edges (long inputs, slow network, auth matrix, idempotency, observability spans, the 403/404 tenant-leak), fixes every gap or bug found, then captures the working trajectory as a permanent Playwright spec or test file before declaring done. Ten-minute budget.

`/flagrare:staleness-audit` diffs your staged changes against the repo's documentation surfaces (README, ADRs, public exports, doc comments, test names, changesets) and flags drift before it lands in history.

`/flagrare:implementation-review` launches six parallel subagents: plan-gap detection, use-case coverage, missing test scenarios, test philosophy (Kent Dodds Testing Trophy), SOLID violations, and Clean Code violations.

`/flagrare:wrap-up` runs automated checks (tests, lint, types), invokes `/flagrare:implementation-review`, then layers additional SOLID and Clean Code review for anything not covered. The combined report tells you whether to commit or fix first.

`/flagrare:release-check` detects the project's release mechanism, decides whether a release is due, and drafts a semver bump with a value-focused changelog entry.

### Review

`/flagrare:pr-reviewer` fetches linked Jira tickets, Figma designs, and Notion docs via MCP, spawns five parallel subagents for systematic code review (correctness, security, tests, SOLID, clean code), then drafts friendly, humanized GitHub-ready comments you can paste directly.

`/flagrare:open-pr` creates a pull request that follows the repo's PR template. It reads `.github/PULL_REQUEST_TEMPLATE.md`, fetches linked tickets for context (tracker-agnostic), and fills each section with narrative prose (not file enumerations). Descriptions explain what changed from both a product and code perspective, link relevant tickets, and include specific testing notes.

### Implementation support

`/flagrare:figma-matcher` enforces pixel-perfect implementation of Figma designs. It extracts every visual property from Figma, spins up Chrome DevTools to measure the current implementation, builds a comparison checklist, and fixes all discrepancies in a single pass.

`/flagrare:research-catalog` fires whenever you do external research (WebFetch, WebSearch, Explore-agent). It catalogs sources under `docs/research/` in the consuming project before returning the synthesis, so decisions trace back to evidence.

`/flagrare:write-docs` guides documentation writing using Pinker's classic style, the Diataxis framework, and concrete examples from React, Stripe, and Anthropic's docs.

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
    /flagrare:codebase-explore       (atdd-plan's own pass — stays self-sufficient for standalone use)
[implementation]                 you have a plan, write code
/flagrare:figma-matcher          UI work done, verify against Figma
/flagrare:smoke-test             feature done, validate behaviour against a running app or service
/flagrare:wrap-up                code done, full quality gate
  /flagrare:implementation-review  (six-axis review, called by wrap-up)
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

For most issues, run the canonical heal script — it fixes stale marketplace names, half-installed plugins, missing settings entries, and obsolete caches in one pass:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

| Symptom | Fix |
|---|---|
| `N errors during load` | Run `/doctor` for the exact plugin and error |
| `Plugin X not found in marketplace flagrare-skills` | Run the heal script above |
| Slash commands missing, 0 errors | Run the heal script above — most often the plugin is enabled but not installed |
| Marketplace operation hangs | Run the heal script above — it cleans the marketplace and re-clones from GitHub |
| `/flagrare:update` runs old logic | You're on a pre-1.3 cached skill. Run the heal script above once; future `/flagrare:update` calls work correctly |
