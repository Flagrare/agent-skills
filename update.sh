#!/usr/bin/env bash
# Canonical install / update / heal script for the flagrare-skills marketplace.
# Safe to run on any state: fresh box, stale personal install, half-broken
# enabled-but-not-installed, version-drift cache, etc.
set -euo pipefail

CURRENT_NAME="flagrare-skills"
REPO_SOURCE="Flagrare/agent-skills"
LEGACY_NAMES=("personal")
SETTINGS="$HOME/.claude/settings.json"

scrub_settings_entry() {
  local key=$1
  if command -v python3 &>/dev/null && [ -f "$SETTINGS" ]; then
    python3 - "$SETTINGS" "$key" <<'PYEOF'
import json, sys
path, key = sys.argv[1], sys.argv[2]
try:
    with open(path) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)
if data.get("enabledPlugins", {}).pop(key, None) is not None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
PYEOF
  fi
}

# 1. Migrate any legacy marketplace names.
for old in "${LEGACY_NAMES[@]}"; do
  if claude plugin marketplace list 2>/dev/null \
      | grep -qE "^[[:space:]]*❯[[:space:]]+${old}\$"; then
    echo "Migrating marketplace: $old → $CURRENT_NAME"
    claude plugin uninstall "flagrare@${old}" 2>/dev/null || true
    claude plugin disable "flagrare@${old}" 2>/dev/null || true
    claude plugin marketplace remove "$old" 2>/dev/null || true
  fi
  # Scrub the settings entry unconditionally — even if the marketplace
  # was already removed manually, a stale enabledPlugins flag survives.
  scrub_settings_entry "flagrare@${old}"
done

# 2. Refresh the marketplace cache; add it if missing.
if claude plugin marketplace list 2>/dev/null \
    | grep -qE "^[[:space:]]*❯[[:space:]]+${CURRENT_NAME}\$"; then
  claude plugin marketplace update "$CURRENT_NAME"
else
  claude plugin marketplace add "$REPO_SOURCE"
fi

# 3. Install the plugin (fetches source + registers for `plugin update`).
#    `install` is idempotent on already-installed plugins.
claude plugin install "flagrare@${CURRENT_NAME}" 2>/dev/null \
  || claude plugin enable "flagrare@${CURRENT_NAME}" 2>/dev/null \
  || true

# 4. Pull the latest plugin version (no-op if already current).
claude plugin update "flagrare@${CURRENT_NAME}" 2>/dev/null || true

# 5. Prune stale cached versions of the plugin from legacy marketplaces.
for old in "${LEGACY_NAMES[@]}"; do
  legacy_cache="$HOME/.claude/plugins/cache/$old"
  if [ -d "$legacy_cache" ]; then
    rm -rf "$legacy_cache"
    echo "Pruned stale cache: $legacy_cache"
  fi
done

echo "Done. Run /reload-plugins in Claude Code or restart your session."
