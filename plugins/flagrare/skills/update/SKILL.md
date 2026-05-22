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

Run the update script:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/../../update.sh"
```

If the script is not found at that path (e.g. running from a remote install with a stripped layout), fall back to one-shot:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

After running, tell the user:

> Skills updated from GitHub. Run `/reload-plugins` or restart Claude Code to apply.
