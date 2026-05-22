---
name: open-pr
description: "Open a pull request that follows the repo's conventions. Reads the PR template from .github/PULL_REQUEST_TEMPLATE.md, fills it with contextualized content (not enumerations), links tracker tickets, writes testing notes, and uses /flagrare:write-docs style for the description. Use when the user says 'open a pr', 'create pr', 'push and pr', 'submit this', 'open pull request', or any variation. Also triggers when code is ready to ship and the user wants to get it reviewed."
---

# Open PR

Create a pull request that reads like a human wrote it.

The goal is a PR description that a reviewer can scan in 30 seconds and understand: what changed, why, and how to verify it works. No file-by-file enumerations. No bullet-point dumps of every touched line. Context and narrative.

---

## Workflow

### Step 1: Understand what happened

Gather the raw material:

```bash
git log --oneline $(git merge-base HEAD main)..HEAD
git diff --stat $(git merge-base HEAD main)..HEAD
git diff $(git merge-base HEAD main)..HEAD
```

Also check the branch name for a ticket key (e.g., `SKU-478/fix-menu-disabled`).

### Step 2: Read the repo's PR template

```bash
cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null || cat .github/pull_request_template.md 2>/dev/null
```

If no template exists, use a minimal structure: title, description, testing notes. But most repos have one, and following it exactly is non-negotiable. The template is the contract between author and reviewer.

### Step 3: Fetch linked context

If a ticket key was found (branch name, commit messages, or user-provided):

1. Fetch the ticket via the best available tool (MCP for the tracker platform, CLI, or WebFetch). Use the same detection logic as `/flagrare:intake` Step 0.
2. Use the ticket's title, description, and acceptance criteria to explain the "why" in the PR description.

If a design link (Figma, etc.) appears in the ticket, note it in the PR for visual reference.

### Step 4: Write the PR body

Fill the template section by section. For each section, the principle is the same: write like you're explaining this to a teammate over coffee, not generating a report.

**Title:** Short, imperative. Under 70 characters. Prefixed with ticket key if the repo convention does that.

**Description sections:**

- **What changed (product perspective):** One paragraph. What does the user/partner/admin experience differently after this merges? Not "changed line 47 of MenuSelector" but "newly created menus now appear active in the selector instead of incorrectly showing as disabled."

- **What changed (code perspective):** Brief technical summary. Which decision did you make and why? Mention the approach, not every file. "Switched the disabled-state derivation from `published` to `enabled` in the dropdown component, since `published` is ClassPass-controlled and shouldn't affect partner-facing status."

- **Testing:** How you verified this works. Be specific: "Ran the full SkuItems test suite (398 tests passing). Added 4 new test cases covering the enabled/published separation." If you tested in a browser or dev environment, say so.

- **Checklist items:** Check off what applies, leave unchecked what doesn't. Don't delete template items (reviewers use them as a reference).

### Step 5: Push and create the PR

```bash
git push -u origin HEAD
gh pr create --title "<title>" --body "$(cat <<'EOF'
<filled template>
EOF
)"
```

If the branch already has a remote and a PR exists, update it instead:
```bash
gh pr edit <number> --body "$(cat <<'EOF'
<filled template>
EOF
)"
```

### Step 6: Report back

Show the user the PR URL and a brief summary of what was submitted. Don't reprint the entire body.

---

## Writing style for PR descriptions

These principles make the difference between a PR that gets reviewed in 5 minutes and one that sits for days:

- **Contextualize, don't enumerate.** "Fixed the disabled state logic" beats "Changed line 47, renamed variable on line 83, updated PropTypes on line 131."
- **Explain decisions.** If you chose approach A over approach B, say why in one sentence. Reviewers wonder about alternatives.
- **Link, don't repeat.** If the ticket has a detailed root cause analysis, link to it. Don't copy-paste the entire ticket into the PR.
- **Testing should build confidence.** "All tests pass" is baseline. Add what specifically validates the fix: edge cases covered, manual verification steps, before/after behavior.
- **Short paragraphs.** Walls of text don't get read. 2-3 sentences per section is ideal.

---

## Anti-patterns

- Don't skip the template. Even if it feels overkill for a one-line fix, fill it in. Consistency matters more than brevity.
- Don't list every changed file. That's what the diff is for.
- Don't write "various improvements" or "code cleanup." Be specific about what and why.
- Don't create the PR without pushing first. Check `git status` for uncommitted work.
- Don't guess the base branch. Detect it from the repo's default (`main`, `master`, `develop`).

---

## Flow position

```
[implementation complete]
     |
     v
/flagrare:wrap-up        <- quality gate
     |
     v
/flagrare:open-pr        <- THIS SKILL
     |
     v
[reviewer picks it up]
```
