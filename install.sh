#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="Flagrare/agent-skills"
PLUGINS=(
  intake
  research-catalog
  atdd-plan
  staleness-audit
  implementation-review
  release-check
  write-docs
)

echo "Adding marketplace..."
claude plugin marketplace add "$MARKETPLACE"

echo "Enabling plugins..."
for plugin in "${PLUGINS[@]}"; do
  claude plugin enable "${plugin}@personal" 2>/dev/null || true
done

echo "Done. Run /reload-plugins in Claude Code or restart your session."
