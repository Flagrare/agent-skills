#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# install.sh is just update.sh with a friendlier "first time" prelude.
# Both flows do the same thing: migrate any stale name, refresh the
# marketplace, enable the plugin.
bash "$SCRIPT_DIR/update.sh"

echo ""
echo "Skills available as:"
echo "  /flagrare:intake"
echo "  /flagrare:atdd-plan"
echo "  /flagrare:codebase-explore"
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
