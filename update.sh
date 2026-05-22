#!/usr/bin/env bash
set -euo pipefail

# Migration: older installs named the marketplace 'personal'.
# Detect any marketplace pointing at this repo under a stale name and
# fix it before refreshing.
if claude plugin marketplace list 2>/dev/null | grep -q "Flagrare/agent-skills"; then
  old_name=$(claude plugin marketplace list 2>/dev/null \
    | awk '/❯/{name=$2} /Flagrare\/agent-skills/{print name; exit}')
  if [ -n "$old_name" ] && [ "$old_name" != "flagrare-skills" ]; then
    echo "Migrating marketplace name: $old_name → flagrare-skills"
    claude plugin disable "flagrare@${old_name}" 2>/dev/null || true
    claude plugin marketplace remove "$old_name" 2>/dev/null || true
    if command -v python3 &>/dev/null; then
      python3 - "$HOME/.claude/settings.json" "$old_name" <<'PYEOF'
import json, sys
path, old = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
data.get("enabledPlugins", {}).pop(f"flagrare@{old}", None)
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
    fi
  fi
fi

# Refresh the marketplace cache if it exists; otherwise add it.
# Either path leaves other plugins untouched.
claude plugin marketplace update flagrare-skills 2>/dev/null \
  || claude plugin marketplace add Flagrare/agent-skills

# Ensure flagrare is enabled (idempotent).
claude plugin enable "flagrare@flagrare-skills" 2>/dev/null || true

echo "Done. Run /reload-plugins in Claude Code or restart your session."
