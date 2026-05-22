---
name: pr-reviewer
description: "Review pull requests with full context. Fetches linked Jira tickets, Figma designs, and Notion docs via MCP, spawns parallel subagents for systematic code review (correctness, security, tests, SOLID, clean code), then drafts friendly, humanized GitHub-ready comments. Use when reviewing PRs, examining code changes, or when the user asks for a code review."
---

# PR Reviewer

Reviews pull requests systematically with full context awareness and humanized feedback.

This skill fetches linked resources via MCP, spawns parallel review subagents for systematic analysis, then synthesises findings into friendly, GitHub-ready comment drafts.

---

## When to Use

- User asks to review a PR, code changes, or diff
- User shares a PR link or number
- User asks "review this", "what do you think of these changes", "check this PR"
- User provides a GitHub PR URL

---

## Workflow

### Step 1: Identify the PR

Parse the PR from user input:
- GitHub URL: extract owner, repo, PR number
- PR number: use current repo context
- Branch name: find associated PR via `gh pr list`

Fetch the PR details:
```bash
gh pr view <number> --json title,body,files,commits,labels,baseRefName,headRefName
gh pr diff <number>
```

### Step 2: Extract and Fetch Linked Resources via MCP

Scan the PR title, description, branch name, and commit messages for linked resources.

**Jira/Atlassian tickets:**

Extract ticket IDs matching `[A-Z]+-[0-9]+` (e.g. `SKU-123`, `CORE-3211`).

1. Call `getAccessibleAtlassianResources` to obtain `cloudId`
2. For each ticket key, call `getJiraIssue` with `cloudId` and `issueIdOrKey`
3. Use the ticket's summary, description, and acceptance criteria to verify alignment

**Figma links:**

Extract URLs matching `figma.com/design/:fileKey/:fileName?node-id=...`

1. Parse `fileKey` and `nodeId` (convert `-` to `:` in node-id)
2. Call `get_design_context` with `fileKey` and `nodeId`
3. Optionally call `get_screenshot` for visual reference

**Notion docs:**

Extract URLs matching `*.notion.so/...` or `*.notion.site/...`

1. Call the Notion MCP to fetch page content
2. Use for requirements, API specs, or architecture decisions

**If MCP fails:**

Note it in the review: "Could not fetch Jira ticket CORE-3211 (Atlassian MCP unavailable). Review based on PR description only." Proceed with available context.

### Step 3: Systematic Code Review (parallel subagents)

Spawn **five review subagents in parallel**. Each receives the full PR diff and returns findings.

Do not run these checks sequentially. Spawn all five simultaneously, collect results, then synthesise.

---

#### Subagent 1: Correctness & Logic

**Inputs:** full PR diff, PR description, linked ticket acceptance criteria.

For every changed function/method:
- Does the logic match the stated intent (from PR description and ticket)?
- Are there off-by-one errors, missing null checks, unhandled branches?
- Are edge cases covered: empty input, boundary values, error paths?
- Are there race conditions or ordering assumptions?
- Does the change break any existing callers?

---

#### Subagent 2: Security

**Inputs:** full PR diff, file list.

Scan for OWASP Top 10 patterns:
- Injection (SQL, command, XSS, template)
- Broken authentication / authorization checks
- Sensitive data exposure (logging secrets, hardcoded keys)
- Missing input validation at system boundaries
- Insecure deserialization
- Overly permissive CORS or CSP
- Dependencies with known vulnerabilities (if lockfile changed)

Only flag issues with concrete exploit paths, not theoretical risks.

---

#### Subagent 3: Test Coverage & Quality

**Inputs:** full PR diff (test files and non-test files).

For every behavior introduced or changed:
- Is there at least one test that exercises it through the public API?
- Do tests assert on observable behavior or implementation internals?
- Are test names descriptive of the behavior being tested?
- Missing scenarios: happy path, empty/nil, boundary, error path, idempotency?
- Do tests mock only at genuine external boundaries (network, clock, OS)?
- Testing Trophy shape: more integration tests than unit tests for cross-unit behavior?

---

#### Subagent 4: SOLID & Architecture

**Inputs:** non-test source files from the PR diff.

- **S**: Does any new class/module have more than one reason to change?
- **O**: Does adding a new variant require modifying existing code?
- **L**: Does any subtype violate its base type's contract?
- **I**: Are there fat interfaces forcing unused method implementations?
- **D**: Are concrete dependencies hardcoded where abstractions would be natural?

Also check: does the change follow the repository's existing architectural patterns, or does it introduce a novel pattern without justification?

---

#### Subagent 5: Clean Code & Conventions

**Inputs:** full PR diff, project CLAUDE.md / DEVELOPMENT_GUIDELINES.md (if they exist).

- Magic values without named constants
- Functions doing more than one thing
- Generic unqualified names (`data`, `info`, `handler`, `manager`)
- Comments that restate the code (keep only "why" comments)
- Half-finished surfaces (TODOs, stub bodies, "implement later")
- Long parameter lists (>3-4 positional params)
- Style violations against project guidelines (if documented)
- Inconsistency with patterns used elsewhere in the same codebase

---

### Step 4: Contextual Review (from MCP-fetched resources)

Layer additional review based on the fetched context:

**Ticket alignment:**
- Do the changes implement what the ticket describes?
- Are all acceptance criteria met?
- Is there scope creep (changes beyond ticket scope)?

**Design alignment (if Figma fetched):**
- Does the implementation match the design?
- Are spacing, colors, states, and interactions correct?
- Are all design states handled (empty, loading, error, success)?

**Doc alignment (if Notion/Confluence fetched):**
- Does the implementation match documented specs?
- Are API contracts followed?
- Are architectural decisions respected?

### Step 5: Draft Humanized GitHub Comments

For every finding (from both systematic review and contextual review), produce a GitHub-ready comment draft.

**Severity scale:**

| Severity | Symbol | Meaning |
|----------|--------|---------|
| Critical | CRITICAL | Must fix before merge: bugs, security, broken behavior |
| Suggestion | SUGGESTION | Should consider: quality, clarity, maintainability |
| Nice to have | NICE | Optional improvement |

**Comment requirements:**
- 1-2 sentences max for inline comments
- Copy-paste ready for GitHub
- Sound like a friendly teammate, not a bot or a gatekeeper
- No AI-isms: avoid "consider", "it would be beneficial", "enhance", "leverage", "crucial", "pivotal"
- Use "you" when it fits
- Frame suggestions as options: "One option:", "Worth adding:", "Might be cleaner to..."
- Reserve firm language for actual blockers only

**Humanization rules (apply to every comment):**
- No em dashes. Use commas, periods, or parentheses.
- No rule of three.
- No "Additionally", "Furthermore", "Moreover".
- No sycophancy ("Great approach!", "Excellent work!").
- Be specific. "Add a null check here" beats "It might be worth considering adding a null check to improve robustness."
- Sound conversational. "Pretty sure this is a typo" beats "Table name typo: it is X everywhere else in this repo."

**Format per finding:**

```
CRITICAL - `path/to/File.kt` L45
GitHub comment: `venue` can be null here. Add a safe call or null check.

SUGGESTION - `reservations/BookingService.kt` L32
GitHub comment: This method's doing a lot. Might be cleaner to pull the validation into its own function.

NICE - `reservations/BookingServiceTest.kt` (file-level)
GitHub comment: Worth adding a test for the cancelled path.
```

### Step 6: Present the Review

```
## PR Review: <PR title>

### Context Fetched
- Jira: <ticket key> - <summary> (or "not linked" / "MCP unavailable")
- Figma: <file/frame> (or "not linked")
- Notion: <page> (or "not linked")

### Overall Assessment
[One paragraph: what the PR does, whether it aligns with the ticket/design, and the verdict: approve / approve with feedback / needs work]

### Findings

[All findings grouped by file, each with severity and GitHub comment draft]

### Checklist
- [ ] Logic correct and edge cases handled
- [ ] No security issues
- [ ] Tests cover new/changed behavior
- [ ] Code follows project conventions
- [ ] PR description explains what and why
- [ ] Ticket acceptance criteria met
- [ ] Design alignment verified (if applicable)
```

---

## Anti-patterns

- Don't review without fetching linked resources. The ticket and design ARE the spec.
- Don't give vague feedback. "This could be better" is useless. Say what to change.
- Don't nitpick formatting if tooling handles it.
- Don't sound like a checklist or a formal audit.
- Don't post comments to the PR without explicit user approval. Always draft first.
- Don't run subagents sequentially. The whole point is parallel dispatch.

---

## Flow position

```
[PR created or shared]
     |
     v
/flagrare:pr-reviewer
     |--- Step 1-2: fetch PR + linked resources (Jira, Figma, Notion)
     |--- Step 3: 5 parallel subagents (correctness, security, tests, SOLID, clean code)
     |--- Step 4: contextual review (ticket/design/doc alignment)
     |--- Step 5: humanize all findings into GitHub comment drafts
     |--- Step 6: present combined review
     |
     v
[user approves posting or adjusts]
```
