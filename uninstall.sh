#!/usr/bin/env bash
set -euo pipefail

echo "Disabling flagrare plugin..."
claude plugin disable "flagrare@flagrare-skills" 2>/dev/null || true

echo "Removing marketplace..."
claude plugin marketplace remove flagrare-skills 2>/dev/null || true

echo "Done. Restart Claude Code or run /reload-plugins to apply."
