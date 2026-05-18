# agent-skills

Personal agent skill library. Each plugin is a slash command available in any Claude Code session once the marketplace is registered.

## Setup

Merge this block into `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "personal": {
      "source": { "source": "github", "repo": "Flagrare/agent-skills" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "intake@personal": true,
    "research-catalog@personal": true,
    "atdd-plan@personal": true,
    "staleness-audit@personal": true,
    "implementation-review@personal": true,
    "release-check@personal": true
  }
}
```

Restart Claude Code (or run `/reload-plugins`). The six slash commands become active and the marketplace updates on every startup.

### Developer mode (for editing skills locally)

If you want to iterate on these skills and test changes without pushing:

```bash
git clone git@github.com:Flagrare/agent-skills.git ~/Dev/agent-skills
mkdir -p ~/.claude/plugins/marketplaces
ln -s ~/Dev/agent-skills ~/.claude/plugins/marketplaces/personal
```

Then **remove the `extraKnownMarketplaces` block** from `settings.json` (keep `enabledPlugins`). The symlink takes over as the marketplace source, and your edits become live after `/reload-plugins`.

## Skills

| Skill | When to invoke |
|---|---|
| `/intake` | When given a ticket — reads the ticket via MCP/CLI, follows all references in parallel subagents, builds a context brief, clarifies ambiguities, then calls `/atdd-plan` |
| `/research-catalog` | After any external research (WebFetch, WebSearch, Explore-agent) — catalogs sources and findings under `docs/research/` before returning the synthesis, creating a traceable link from decision back to evidence |
| `/atdd-plan` | Before any feature, fix, or refactor — ATDD-first plan with design patterns, SOLID audit, and gap review |
| `/staleness-audit` | Before every commit — docs drift check across README, ADRs, exports, TSDoc, changesets, test names |
| `/implementation-review` | Before every commit, after `/staleness-audit` — six parallel subagents: plan gaps, use-case coverage, test scenarios, test philosophy, SOLID, Clean Code |
| `/release-check` | After every commit — checks if a release is due and drafts a value-focused CHANGELOG entry (Valve Dota style) |

> The planning skill is exposed as `/atdd-plan` rather than `/plan` to avoid clashing with Claude Code's built-in plan mode and the `superpowers:writing-plans` skill.

## Full workflow

```
/intake [ticket ID or URL]
     ↓ parallel subagents read ticket + all references
     ↓ /research-catalog  ← log external sources before synthesising
     ↓ context brief + clarifying questions
     ↓
/atdd-plan               ← /research-catalog again if plan requires external research
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
