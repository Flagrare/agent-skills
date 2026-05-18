# agent-skills

Personal agent skill library. Each plugin is a slash command available in any Claude Code session once the marketplace is linked.

## Setup

```bash
git clone https://github.com/Flagrare/agent-skills ~/Dev/agent-skills
ln -s ~/Dev/agent-skills ~/.claude/plugins/marketplaces/personal
```

## Skills

| Skill | When to invoke |
|---|---|
| `/plan` | Before any feature, fix, or refactor — ATDD-first plan with design patterns, SOLID audit, and gap review |
| `/staleness-audit` | Before every commit — docs drift check across README, ADRs, exports, TSDoc, changesets, test names |
| `/implementation-review` | Before every commit, after `/staleness-audit` — plan gaps, use-case coverage, test scenarios, test philosophy, SOLID, Clean Code |
| `/release-check` | After every commit — checks if a release is due and drafts a value-focused CHANGELOG entry (Valve Dota style) |

## Commit flow

```
[code changes complete]
     ↓
/staleness-audit
     ↓
/implementation-review
     ↓
git commit
     ↓
/release-check
```
