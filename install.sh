#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="Flagrare/agent-skills"

echo "Adding marketplace..."
claude plugin marketplace add "$MARKETPLACE"

echo "Enabling flagrare plugin..."
claude plugin enable "flagrare@personal" 2>/dev/null || true

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
