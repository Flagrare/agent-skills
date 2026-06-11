---
name: wrap-up
description: "Post-implementation quality gate. Runs automated checks (tests, lint, types), invokes /flagrare:implementation-review for the six-check parallel review, then performs additional SOLID and Clean Code review on any findings not covered. Use when the user says 'wrap up', 'review changes', 'check my work', 'am I done', or after completing an implementation task."
---

# Wrap-up

Validate implementation quality through automated checks and structured review.

This skill orchestrates automated tooling and the `/flagrare:implementation-review` skill, then layers additional quality checks on top.

---

## When to Use

1. User says "wrap up", "review changes", "check my work", "am I done", "did I miss anything"
2. After completing a todo item or implementation task
3. Before committing (remind the user: "Ready for wrap-up?")

---

## Workflow

### Step 1: Run Automated Checks

Detect and run the project's test, lint, and typecheck commands.

**Detection order:**

1. Check `package.json` for scripts
2. Check `build.gradle.kts` / `build.gradle` for tasks
3. Check `pyproject.toml` for tool configs
4. Check `Makefile` for targets
5. Check common config files (`.eslintrc`, `tsconfig.json`, `pytest.ini`, etc.)

**Common commands by stack:**

| Stack | Test | Lint | Typecheck |
|-------|------|------|-----------|
| Node (npm) | `npm test` | `npm run lint` | `npm run typecheck` or `npx tsc --noEmit` |
| Node (pnpm) | `pnpm test` | `pnpm lint` | `pnpm typecheck` |
| Kotlin/Gradle | `./gradlew test` | `./gradlew ktlintCheck` | (built into compiler) |
| Python | `pytest` | `ruff check .` or `flake8` | `mypy .` or `pyright` |
| Go | `go test ./...` | `golangci-lint run` | (built into compiler) |

**Execute all three, continue even if one fails:**

```bash
{test_cmd} ; {lint_cmd} ; {typecheck_cmd}
```

**Report failures clearly:**

```
## Automated Checks

| Check | Status | Issues |
|-------|--------|--------|
| Tests | PASS | - |
| Lint | FAIL | 3 errors in `src/utils.ts` |
| Types | PASS | - |
```

If any check fails, list the specific errors.

### Step 2: Invoke `/flagrare:implementation-review`

Call `/flagrare:implementation-review`. This runs six parallel subagent checks:

1. Plan gap analysis
2. Use-case coverage
3. Missing test scenarios
4. Test philosophy (Kent Dodds Testing Trophy)
5. SOLID violations
6. Clean Code violations

Checks 2–4 apply `/flagrare:testing-philosophy` — behavior over implementation and the e2e necessity floor — so test quality is owned there; don't re-litigate it in Step 3.

**Wait for it to complete.** Collect all findings.

### Step 3: Additional Review (gaps not covered by /flagrare:implementation-review)

After `/flagrare:implementation-review` reports, check for anything it might have missed due to scope. These are supplementary checks, not duplicates.

**Naming review:**
- Are names intention-revealing?
- Do they avoid mental mapping?
- Bad: `d`, `theList`, `hp`, `apts`
- Good: `elapsedDays`, `activeUsers`, `hoursPerTask`, `apartments`

**Function size review:**
- Are functions small (ideally under 20 lines)?
- Do they have few arguments (3 or fewer ideal)?
- Are abstraction levels consistent within a function?

**Error handling review:**
- Are exceptions used instead of error codes?
- Is error handling separated from business logic?
- Are error messages informative?

**Code smells not covered by SOLID:**
- Duplicate code across the diff
- Feature envy (method uses another object's data excessively)
- Data clumps (groups of data that always appear together)
- Primitive obsession (using primitives instead of small objects)
- Long parameter lists without grouping

### Step 4: Generate Combined Report

Merge automated check results, `/flagrare:implementation-review` findings, and supplementary review into one report:

```
## Wrap-up Report

### Automated Checks
| Check | Status |
|-------|--------|
| Tests | PASS/FAIL |
| Lint | PASS/FAIL |
| Types | PASS/FAIL |

### Implementation Review (from /flagrare:implementation-review)
[Paste the six-check summary verbatim]

### Supplementary Review

#### Good
- {aspect}: {what's done well}

#### Suggestions
- **{aspect}** in `{file}:{line}`: {issue}
  - Suggestion: {how to fix}

### Summary
- {N} blocking issues (must fix)
- {M} suggestions (should consider)
- Overall: Ready to commit / Needs attention
```

### Step 5: Offer Fixes

If issues were found, **close with a tool, not prose.** The Step 4 report is a large artifact; ending with a prose "Would you like me to…" frequently reads as turn-complete and stops before the user can answer (the stall pattern in [`docs/research/2026-06-11-claude-code-goal-anti-stall.md`](../../../../docs/research/2026-06-11-claude-code-goal-anti-stall.md)). Immediately after the report, issue an `AskUserQuestion` tool call with options:

- **Fix the automated check errors** (lint/type)
- **Apply the review suggestions**
- **Both** (Recommended when both surfaced findings)
- **Skip for now**

Do not render these as a numbered prose list and wait — use the tool so the user gets buttons and the turn doesn't end ambiguously.

---

## Anti-patterns

- Don't skip automated checks. They catch things review cannot.
- Don't duplicate what `/flagrare:implementation-review` already covers. If it reported on SOLID, don't re-report the same finding.
- Don't block on advisory findings. Use judgment on what's blocking vs nice-to-have.
- Don't skip this because "the change is small". Small changes still break things.

---

## Flow position

```
[code changes complete]
     |
     v
/flagrare:wrap-up
     |--- Step 1: automated checks (tests, lint, types)
     |--- Step 2: /flagrare:implementation-review (6 parallel subagents)
     |--- Step 3: supplementary review
     |--- Step 4: combined report
     |
     v
git commit
     |
     v
/flagrare:release-check
```
