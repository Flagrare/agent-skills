# agent-skills

Sixteen skills that wrap around your development cycle in Claude Code. They turn tickets into ATDD plans, guard commits against doc drift, run six-axis code review, draft changelogs that read like patch notes, and review PRs with full context from your tracker and design tools.

All skills are namespaced under `flagrare:*` to avoid collisions with other plugins. Installing this marketplace adds `/flagrare:intake`, `/flagrare:work-prep`, `/flagrare:wrap-up`, `/flagrare:pr-reviewer`, and twelve more to every Claude Code session.

## Install

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/install.sh)
```

One command. It registers the marketplace, enables the `flagrare` plugin, and makes all sixteen skills available. Restart Claude Code or run `/reload-plugins` afterward.

If you prefer to clone first:

```bash
git clone git@github.com:Flagrare/agent-skills.git && ./agent-skills/install.sh
```

## What each skill does

### Planning and context

`/flagrare:intake` reads a ticket (via Jira MCP, Linear, GitHub CLI, or a pasted URL), dispatches parallel subagents to follow every linked doc and PR, and assembles a context brief. It asks clarifying questions, then hands off to `/flagrare:atdd-plan`.

`/flagrare:atdd-plan` produces an implementation plan rooted in acceptance tests. It invokes `/flagrare:codebase-explore` for codebase understanding, names design patterns, runs a SOLID audit, identifies gaps, and outputs a structured plan.

`/flagrare:work-prep` orchestrates the full ticket-to-plan workflow. It calls `/flagrare:intake` first for context gathering and clarifying questions, then `/flagrare:atdd-plan` which explores the codebase via `/flagrare:codebase-explore` and produces an ATDD-first implementation plan. One command from ticket to plan.

`/flagrare:codebase-explore` maps conventions, reusable utilities, analogous features, and data flows for a planned change. Returns raw findings only (no plan, no tests). Used by `/flagrare:atdd-plan` as its codebase understanding step, or standalone when you need to understand a feature area.

`/flagrare:tdd-writer` drafts Technical Design Documents for large projects (2+ weeks). It fetches context from Jira, Confluence, Figma, and Notion via MCP, analyzes the actual codebase, and marks every unverified claim explicitly. Nothing is assumed.

`/flagrare:ticket-creator` writes well-structured tickets as reviewable markdown files, then pushes to any tracker (Jira, Linear, GitHub Issues, Shortcut, Asana, Trello) via MCP or CLI after you review and approve.

### Quality gates

`/flagrare:staleness-audit` diffs your staged changes against the repo's documentation surfaces (README, ADRs, public exports, doc comments, test names, changesets) and flags drift before it lands in history.

`/flagrare:implementation-review` launches six parallel subagents: plan-gap detection, use-case coverage, missing test scenarios, test philosophy (Kent Dodds Testing Trophy), SOLID violations, and Clean Code violations.

`/flagrare:wrap-up` runs automated checks (tests, lint, types), invokes `/flagrare:implementation-review`, then layers additional SOLID and Clean Code review for anything not covered. The combined report tells you whether to commit or fix first.

`/flagrare:release-check` detects the project's release mechanism, decides whether a release is due, and drafts a semver bump with a value-focused changelog entry.

### Review

`/flagrare:pr-reviewer` fetches linked Jira tickets, Figma designs, and Notion docs via MCP, spawns five parallel subagents for systematic code review (correctness, security, tests, SOLID, clean code), then drafts friendly, humanized GitHub-ready comments you can paste directly.

### Implementation support

`/flagrare:figma-matcher` enforces pixel-perfect implementation of Figma designs. It extracts every visual property from Figma, spins up Chrome DevTools to measure the current implementation, builds a comparison checklist, and fixes all discrepancies in a single pass.

`/flagrare:research-catalog` fires whenever you do external research (WebFetch, WebSearch, Explore-agent). It catalogs sources under `docs/research/` in the consuming project before returning the synthesis, so decisions trace back to evidence.

`/flagrare:write-docs` guides documentation writing using Pinker's classic style, the Diataxis framework, and concrete examples from React, Stripe, and Anthropic's docs.

### Maintenance

`/flagrare:update` pulls the latest skills from GitHub by refreshing the marketplace cache. Run it whenever you want the newest version of any skill.

`/flagrare:uninstall` removes the flagrare plugin and marketplace registration. Run it to cleanly disable all skills.

## Workflow

A typical feature cycle:

```
/flagrare:work-prep [ticket]     you have a ticket, need context + plan
  /flagrare:intake                 (context gathering, called by work-prep)
  /flagrare:atdd-plan              (codebase exploration + plan, called by work-prep)
    /flagrare:codebase-explore       (codebase exploration, called by atdd-plan)
[implementation]                 you have a plan, write code
/flagrare:figma-matcher          UI work done, verify against Figma
/flagrare:wrap-up                code done, full quality gate
  /flagrare:implementation-review  (six-axis review, called by wrap-up)
/flagrare:staleness-audit        docs didn't drift
git commit                       everything passes, commit
/flagrare:release-check          committed, decide if a release ships
```

`/flagrare:research-catalog` slots in wherever external research happens. `/flagrare:pr-reviewer` runs when reviewing someone else's PR. `/flagrare:tdd-writer` and `/flagrare:ticket-creator` run during planning phases for larger projects. `/flagrare:update` refreshes skills from GitHub; `/flagrare:uninstall` removes everything cleanly.

## Developing skills locally

If you want to edit these skills and see changes without pushing to GitHub:

```bash
git clone git@github.com:Flagrare/agent-skills.git ~/Dev/agent-skills
claude plugin marketplace remove personal
claude plugin marketplace add ~/Dev/agent-skills
```

After this, edits in `~/Dev/agent-skills` take effect on `/reload-plugins`. To switch back to the published version, reverse the process: remove and re-add with the GitHub path.

## Troubleshooting

Run `/doctor`. It names the specific plugin and the specific failure.

| Symptom | Fix |
|---|---|
| `N errors during load` | Run `/doctor` for the exact plugin and error |
| `Plugin X not found in marketplace personal` | Re-run `claude plugin marketplace add Flagrare/agent-skills` |
| Slash commands missing, 0 errors | Check `~/.claude/settings.json` has `"flagrare@personal": true` |
| Marketplace operation hangs | `claude plugin marketplace remove personal`, then re-add |
