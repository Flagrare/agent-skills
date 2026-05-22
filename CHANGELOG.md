# Changelog

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
