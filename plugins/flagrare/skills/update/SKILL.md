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

Run the canonical update script directly from GitHub. This guarantees
the script logic is current even if this skill's text has been cached
from an older release:

```bash
bash <(curl -sL https://raw.githubusercontent.com/Flagrare/agent-skills/main/update.sh)
```

After running, tell the user:

> Skills updated from GitHub. Run `/reload-plugins` or restart Claude Code to apply.
