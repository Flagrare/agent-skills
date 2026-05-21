# agent-skills

Seven slash commands that wrap around your development cycle in Claude Code. They turn tickets into ATDD plans, guard commits against doc drift, run six-axis code review, and draft changelogs that read like patch notes.

This is a private plugin marketplace. Installing it adds `/intake`, `/atdd-plan`, `/research-catalog`, `/staleness-audit`, `/implementation-review`, `/release-check`, and `/write-docs` to every Claude Code session.

## Install

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/install.sh)
```

One command. It registers the marketplace, fetches the plugins, and enables all seven. Restart Claude Code or run `/reload-plugins` afterward.

If you prefer to clone first:

```bash
git clone git@github.com:Flagrare/agent-skills.git && ./agent-skills/install.sh
```

## What each skill does

`/intake` reads a ticket (via Jira MCP, GitHub CLI, or a pasted URL), dispatches parallel subagents to follow every linked doc and PR, and assembles a context brief. It asks clarifying questions, then hands off to `/atdd-plan`.

`/atdd-plan` produces an implementation plan rooted in acceptance tests. It names design patterns, runs a SOLID audit, identifies gaps, and outputs a structured plan you can execute or hand to `/superpowers:executing-plans`.

`/research-catalog` fires whenever you do external research (WebFetch, WebSearch, Explore-agent). It catalogs sources under `docs/research/` in the consuming project before returning the synthesis, so decisions trace back to evidence.

`/staleness-audit` diffs your staged changes against the repo's documentation surfaces (README, ADRs, public exports, doc comments, test names, changesets) and flags drift before it lands in history.

`/implementation-review` launches six parallel subagents: plan-gap detection, use-case coverage, missing test scenarios, test philosophy (Kent Dodds Testing Trophy), SOLID violations, and Clean Code violations.

`/release-check` detects the project's release mechanism, decides whether a release is due, and drafts a semver bump with a value-focused changelog entry.

`/write-docs` guides documentation writing using Pinker's classic style, the Diataxis framework, and concrete examples from React, Stripe, and Anthropic's docs.

## Workflow

A typical feature cycle looks like this:

```
/intake [ticket]        you have a ticket, need context
/atdd-plan              you have context, need a plan
[implementation]        you have a plan, write code
/staleness-audit        code is done, check docs didn't drift
/implementation-review  docs are clean, check code quality
git commit              everything passes, commit
/release-check          committed, decide if a release ships
```

`/research-catalog` slots in wherever external research happens. It's not a phase; it's a reflex.

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
| Slash commands missing, 0 errors | Check `~/.claude/settings.json` has `"intake@personal": true` (and so on for each plugin) |
| Marketplace operation hangs | `claude plugin marketplace remove personal`, then re-add |
