#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="Flagrare/agent-skills"

# Migration: older versions of this repo named the marketplace 'personal'.
# Detect and clean that up before adding the new 'agent-skills' name.
if claude plugin marketplace list 2>/dev/null | grep -q "Flagrare/agent-skills"; then
  old_name=$(claude plugin marketplace list 2>/dev/null \
    | awk '/❯/{name=$2} /Flagrare\/agent-skills/{print name; exit}')
  if [ -n "$old_name" ] && [ "$old_name" != "agent-skills" ]; then
    echo "Migrating marketplace name: $old_name → agent-skills"
    claude plugin disable "flagrare@${old_name}" 2>/dev/null || true
    claude plugin marketplace remove "$old_name" 2>/dev/null || true
    # Scrub the stale enabledPlugins entry from settings.json
    if command -v python3 &>/dev/null; then
      python3 - "$HOME/.claude/settings.json" "$old_name" <<'PYEOF'
import json, sys
path, old = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
ep = data.get("enabledPlugins", {})
ep.pop(f"flagrare@{old}", None)
data["enabledPlugins"] = ep
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYEOF
    fi
  fi
fi

echo "Adding marketplace..."
claude plugin marketplace add "$MARKETPLACE"

echo "Enabling flagrare plugin..."
claude plugin enable "flagrare@agent-skills" 2>/dev/null || true

echo "Done. Run /reload-plugins in Claude Code or restart your session."
echo ""
echo "Skills available as:"
echo "  /flagrare:intake"
echo "  /flagrare:atdd-plan"
echo "  /flagrare:work-prep"
echo "  /flagrare:wrap-up"
echo "  /flagrare:pr-reviewer"
echo "  /flagrare:tdd-writer"
echo "  /flagrare:ticket-creator"
echo "  /flagrare:figma-matcher"
echo "  /flagrare:staleness-audit"
echo "  /flagrare:implementation-review"
echo "  /flagrare:release-check"
echo "  /flagrare:research-catalog"
echo "  /flagrare:write-docs"
echo "  /flagrare:update"
echo "  /flagrare:uninstall"
