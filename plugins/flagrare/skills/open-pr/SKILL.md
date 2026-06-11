---
name: open-pr
description: "Open a pull request that follows the repo's conventions. Reads the PR template from .github/PULL_REQUEST_TEMPLATE.md, fills it with contextualized content (not enumerations), links tracker tickets, writes testing notes, and uses /flagrare:write-docs style for the description. Use when the user says 'open a pr', 'create pr', 'push and pr', 'submit this', 'open pull request', or any variation. Also triggers when code is ready to ship and the user wants to get it reviewed."
---

# Open PR

Create a pull request that reads like a human wrote it.

The goal is a PR description that a reviewer can scan in 30 seconds and understand: what changed, why, and how to verify it works. No file-by-file enumerations. No bullet-point dumps of every touched line. Context and narrative.

**REQUIRED BACKGROUND:** Invoke `/flagrare:write-docs` before writing the PR body. A PR description is a tiny how-to/explanation doc, and the same craft applies: lead with the reader's situation, let prose carry causality, put context at the point of need. This skill owns *the PR mechanics and the repo's conventions*; write-docs owns *making the prose readable*. The "Writing style" section below applies that craft specifically to PRs — read both.

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

### Step 2: Learn the repo's conventions

A template tells you the *sections*; recently merged PRs tell you the *house style* — how much detail goes in each section, what the title format really is, whether they link tickets a particular way. Read both. This is the step that fixes "PRs that don't follow codebase patterns."

```bash
# The template (the section contract — follow it exactly)
cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null \
  || cat .github/pull_request_template.md 2>/dev/null \
  || ls .github/PULL_REQUEST_TEMPLATE/ 2>/dev/null

# The lived convention — how this team actually writes PRs
gh pr list --state merged --limit 5 --json number,title,body 2>/dev/null
```

Study the merged PRs for the patterns the template can't encode: title prefix style, how much prose each section gets, how they reference tickets and designs, the tone. Match what you see. If template and recent practice disagree, follow the template's structure but borrow the recent PRs' level of detail and voice.

If no template exists, fall back to a minimal structure (title, description, testing notes) shaped like the recent merged PRs. Most repos have a template, and following it exactly is non-negotiable — it's the contract between author and reviewer.

### Step 3: Fetch linked context

If a ticket key was found (branch name, commit messages, or user-provided):

1. Fetch the ticket via the best available tool (MCP for the tracker platform, CLI, or WebFetch). Use the same detection logic as `/flagrare:intake` Step 0.
2. Use the ticket's title, description, and acceptance criteria to explain the "why" in the PR description.

If a design link (Figma, etc.) appears in the ticket, note it in the PR for visual reference.

### Step 4: Write the PR body

Fill the template section by section, applying the write-docs craft from the REQUIRED BACKGROUND above. For each section, the principle is the same: write like you're explaining this to a teammate over coffee, not generating a report. Lead each section with what the reader needs to know, let a sentence carry the *because*, and only use a bullet list when the items are genuinely parallel (a list of independent fixes in one PR, say) rather than a single decision sliced into fragments.

**Anchor to behavior, not coordinates.** Describe *what the code now does* and *why*, never *where the lines moved*. "Line 47", "renamed the variable on line 83", "updated the import block" are all stale the moment you push another commit, and they make the reviewer hunt. The diff already shows the *where*; your job is the *what* and *why*. Likewise, don't transcribe the diff into prose — if a reviewer can get it from the diff, leave it to the diff.

**Title:** Short, imperative. Under 70 characters. Prefixed with ticket key if the repo convention does that.

**Description sections:**

- **What changed (product perspective):** One paragraph. What does the user/partner/admin experience differently after this merges? Not "changed line 47 of MenuSelector" but "newly created menus now appear active in the selector instead of incorrectly showing as disabled."

- **What changed (code perspective):** Brief technical summary. Which decision did you make and why? Mention the approach, not every file. "Switched the disabled-state derivation from `published` to `enabled` in the dropdown component, since `published` is ClassPass-controlled and shouldn't affect partner-facing status."

- **Testing:** What you did to convince yourself it works — the *kind* of verification, not a scoreboard. "Created a new menu in the dashboard and confirmed it shows as active and selectable; checked that an existing ClassPass-disabled menu still greys out. Added tests covering the enabled-vs-published split." Name the behaviors you exercised and any manual/browser check. **Do not include test counts, coverage percentages, or "N tests passing"** — those numbers rot on the next commit, nobody reads them, and CI already reports them.

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
- **Testing should build confidence, not keep score.** Say *what behavior you verified and how* — the edge cases you exercised, the manual/browser steps, the before/after. Skip test counts, coverage %, and "N passing" entirely: they're churn that's stale by the next push and the reader doesn't care; CI is the source of truth for the numbers.
- **Short paragraphs.** Walls of text don't get read. 2-3 sentences per section is ideal.

A before/after, since the example is what the model imitates:

> ❌ Enumerated, stale, contextless:
> *"Updated MenuSelector.tsx. Changed line 47 disabled logic. Renamed `pub` to `enabled` on line 83. Updated PropTypes. Ran 398 tests, all passing. Added 4 tests. Coverage 91% → 92%."*
>
> ✅ Context-first prose:
> *"Newly created menus were showing as disabled in the selector even though they were active. The selector was deriving its disabled state from `published`, which ClassPass controls — so a partner's brand-new menu looked unusable until ClassPass flipped a flag. This switches the derivation to `enabled`, the partner-facing field, so a menu is selectable the moment it's created. Verified by creating a menu and confirming it's immediately selectable, and that a genuinely unpublished one still greys out."*

The bad version lists what moved; the good version explains what was wrong, why, what changed, and how it was checked — and it won't rot, because there's not a single coordinate or count in it.

---

## Anti-patterns

- Don't skip the template. Even if it feels overkill for a one-line fix, fill it in. Consistency matters more than brevity.
- Don't enumerate where you should narrate. A description made of five-bullet lists has flattened all the causality out of your change. If the bullets depend on each other, write the paragraph.
- Don't reference line numbers or file coordinates ("changed line 47"). They go stale on the next push and the diff already shows them. Anchor to behavior.
- Don't include churn-y numbers that rot and that nobody reads: test counts ("398 tests passing"), coverage percentages, "N tests added", file-change counts. CI reports the numbers; the PR body is for context. Say *what* you verified, never *how many*.
- Don't list every changed file. That's what the diff is for.
- Don't write "various improvements" or "code cleanup." Be specific about what and why.
- Don't ignore the repo's lived style. Skipping the recent-merged-PR check in Step 2 is how PRs end up not matching house conventions.
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
