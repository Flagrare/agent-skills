#!/usr/bin/env bash
# Shared scaffold for the cases that start from an installed setup (remove, status, tune):
# installs fixtures/installed-config.json into the run's throwaway HOME.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.claude"
[ -f "$HOME/.claude/settings.json" ] || echo '{"outputStyle": "Explanatory"}' > "$HOME/.claude/settings.json"
python3 "$here/../../skills/communication-setup/scripts/setup.py" install "$here/fixtures/installed-config.json" --home "$HOME"
