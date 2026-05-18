# agent-skills

Personal agent skill library. Each plugin is a slash command available in any Claude Code session once the marketplace is added and the plugins enabled.

## Install

Two steps. Both required — neither alone is sufficient.

**1. Register and clone the marketplace:**

```bash
claude plugin marketplace add Flagrare/agent-skills
```

This declares the marketplace in `~/.claude/settings.json` (under `extraKnownMarketplaces`) **and** fetches the plugin manifests into the local cache. The CLI is the only way to trigger the initial fetch — adding `extraKnownMarketplaces` by hand registers the marketplace but does not pull its contents.

**2. Enable the six skills.** Merge into `~/.claude/settings.json`:

```json
{
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

Then either restart Claude Code or run `/reload-plugins` in any session.

## Verify

After reload, expect Claude Code to report **6 additional plugins** with **0 errors** on the load line. Test one of the slash commands — type `/atdd-plan` and confirm it appears as an option. If it does, you're done.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `N errors during load` after reload | One layer of the install pipeline (registration, clone, enablement) is incomplete | Run `/doctor` for specifics |
| `Plugin X not found in marketplace personal` | Marketplace registered but contents not cloned | Re-run `claude plugin marketplace add Flagrare/agent-skills` |
| 0 errors but slash commands missing | `enabledPlugins` entries missing or mistyped | Check that each entry is `<plugin>@personal` exactly (e.g. `atdd-plan@personal`, not `atdd-plan` or `plan@personal`) |
| Marketplace re-clone hangs | Stale lock or partial fetch | `claude plugin marketplace remove personal` then re-add |

`/doctor` is the source of truth for what's broken — it names the specific plugin and the specific failure mode.

## Migrating from the old (symlink) setup

Earlier versions of this README told you to clone the repo and symlink it into `~/.claude/plugins/marketplaces/personal`. That approach silently fails: the symlink gets discovered but no install pipeline runs, so plugins enable into nothing. If you followed those instructions, remove the symlink before installing fresh:

```bash
rm ~/.claude/plugins/marketplaces/personal
```

Then run the two install steps above.

## Developer mode

To edit skills locally and see changes on `/reload-plugins` without push/pull:

```bash
git clone git@github.com:Flagrare/agent-skills.git ~/Dev/agent-skills
claude plugin marketplace remove personal
claude plugin marketplace add ~/Dev/agent-skills
```

This swaps the GitHub source for a local directory source. Edits in `~/Dev/agent-skills` become live after `/reload-plugins`. To switch back to the published version: `claude plugin marketplace remove personal && claude plugin marketplace add Flagrare/agent-skills`.

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
