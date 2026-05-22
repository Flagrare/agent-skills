# Changelog

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
