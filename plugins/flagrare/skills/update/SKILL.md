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

Run:

```bash
claude plugin disable "flagrare@personal" 2>/dev/null || true
claude plugin marketplace remove personal 2>/dev/null || true
claude plugin marketplace add Flagrare/agent-skills
claude plugin enable "flagrare@personal" 2>/dev/null || true
```

After running, tell the user:

> Skills updated from GitHub. Run `/reload-plugins` or restart Claude Code to apply.
