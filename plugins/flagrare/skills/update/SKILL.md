---
name: update
description: "Pull the latest flagrare skills from GitHub. Use when the user says 'update skills', 'refresh skills', 'pull latest skills', 'update flagrare', or 'sync skills'."
---

# Update

Pull the latest version of all flagrare skills from the remote repository.

## When to Use

- User says "update skills", "refresh skills", "pull latest skills", "update flagrare", "sync skills"
- User wants to get the newest version of a skill after a known push

## Procedure

Run the following as a single Bash block:

```bash
# Snapshot all currently-enabled personal plugins before removing the marketplace
enabled_personal=$(jq -r '.enabledPlugins | to_entries[] | select(.key | endswith("@personal")) | select(.value == true) | .key' ~/.claude/settings.json 2>/dev/null)

claude plugin marketplace remove personal 2>/dev/null || true
claude plugin marketplace add Flagrare/agent-skills

# Re-enable every plugin that was enabled before
for plugin in $enabled_personal; do
  claude plugin enable "$plugin" 2>/dev/null || true
done
```

After running, tell the user:

> Skills updated from GitHub. Run `/reload-plugins` or restart Claude Code to apply.
