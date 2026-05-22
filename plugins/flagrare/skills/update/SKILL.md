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
# Refresh the marketplace cache if it exists; otherwise add it.
# Either path leaves other plugins untouched.
claude plugin marketplace update agent-skills 2>/dev/null \
  || claude plugin marketplace add Flagrare/agent-skills

# Ensure flagrare is enabled (idempotent)
claude plugin enable "flagrare@agent-skills" 2>/dev/null || true
```

After running, tell the user:

> Skills updated from GitHub. Run `/reload-plugins` or restart Claude Code to apply.
