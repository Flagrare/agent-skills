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
| `/intake` | When given a ticket — reads the ticket via MCP/CLI, follows all references in parallel subagents, builds a context brief, clarifies ambiguities, then calls `/plan` |
| `/research-catalog` | After any external research (WebFetch, WebSearch, Explore-agent) — catalogs sources and findings under `docs/research/` before returning the synthesis, creating a traceable link from decision back to evidence |
| `/plan` | Before any feature, fix, or refactor — ATDD-first plan with design patterns, SOLID audit, and gap review |
| `/staleness-audit` | Before every commit — docs drift check across README, ADRs, exports, TSDoc, changesets, test names |
| `/implementation-review` | Before every commit, after `/staleness-audit` — six parallel subagents: plan gaps, use-case coverage, test scenarios, test philosophy, SOLID, Clean Code |
| `/release-check` | After every commit — checks if a release is due and drafts a value-focused CHANGELOG entry (Valve Dota style) |

## Full workflow

```
/intake [ticket ID or URL]
     ↓ parallel subagents read ticket + all references
     ↓ context brief + clarifying questions
     ↓
/plan
     ↓
[implementation]
     ↓
/staleness-audit
     ↓
/implementation-review  (6 parallel subagents)
     ↓
git commit
     ↓
/release-check
```
