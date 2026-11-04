#!/usr/bin/env bash
# The user already has a hand-made length hook and their own output style.
set -euo pipefail
mkdir -p "$HOME/.claude/hooks" "$HOME/.claude/output-styles"
printf '#!/usr/bin/env python3\n# blocks long replies\n' > "$HOME/.claude/hooks/reply-length.py"
printf -- '---\nname: Terse\ndescription: short replies\n---\nBe terse.\n' > "$HOME/.claude/output-styles/Terse.md"
cat > "$HOME/.claude/settings.json" <<'JSON'
{"outputStyle": "Terse", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/reply-length.py"}]}]}}
JSON
