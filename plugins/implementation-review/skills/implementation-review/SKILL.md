---
name: implementation-review
description: "Pre-commit quality gate. Invoke before every git commit, after /staleness-audit. Six checks — plan gaps, use-case coverage gaps, missing test scenarios, test philosophy violations (Kent Dodds Testing Trophy), SOLID violations, Clean Code violations. Surfaces findings before they land in history. Also invoke when the user says review this, am I done, did I miss anything, or check the quality."
---

# Implementation Review

Run this before every commit, after `/staleness-audit`. The goal: **what was planned is implemented, what is implemented is tested, and what is tested is correct**.

Don't be lazy — actually read the diff, the plan, and the test files. Each check is a deliberate read and comparison. The whole audit should take under 2 minutes.

---

## Inputs to gather first

Before any check, collect:

- `git diff --staged` — what's about to be committed (the primary input)
- `git diff --staged --name-only` — which files changed
- The **active plan** — look in this order:
  1. Session context: did `/plan` run earlier in this conversation? Use that output.
  2. `~/.claude/plans/*.md` — the most recently modified file is the working plan.
  3. `docs/decisions/` ADRs — for use-case definitions and scope. ADR-0001 is always the mission/scope anchor.
  4. README roadmap — the checked/unchecked roadmap items define what's in scope.
- Test files touched or related to the staged changes.

If no plan is findable, say so explicitly and skip checks 1–2. Do not invent a plan.

---

## Check 1 — Plan gap analysis

Compare what the active plan said would be built against what the staged diff actually implements.

For each item in the plan's "Implementation Phases" or task list:
- Is it in the staged diff? → ✓ implemented
- Is it partially there? → ⚠ partial — what's missing
- Is it absent entirely? → ✗ gap — was it intentionally deferred, or forgotten?

Ask yourself: would a reader of the plan consider this commit "phase complete"? If the plan defined a gate ("Phase N is done when ATs #1–4 pass"), does the commit satisfy it?

Flag every gap. A deferred item is not a gap — but it must be explicitly deferred, not silently absent.

---

## Check 2 — Use-case coverage

Read ADR-0001 (or equivalent mission/scope ADR) and the README's feature description. For every **user-facing capability** in scope for this commit:

- Is there at least one test that exercises it through the public API?
- Is there a code path that implements it?

This is different from Check 1 (plan gaps) — use cases can be implicit in the product scope even if the plan didn't spell them out. Ask: "what would a consumer of this code reasonably expect to be able to do?"

Flag any use case that has an implementation but no test, or a test but no implementation.

---

## Check 3 — Missing test scenarios

For every behavior introduced or changed in the staged diff, work through this scenario checklist:

| Scenario type | Question to ask |
|---|---|
| Happy path | Is the basic success case tested? |
| Empty / nil / zero | What happens when the input is empty, null, zero, or absent? |
| Boundary | First item, last item, exactly one item, max capacity? |
| Invalid input | Malformed, out-of-range, wrong type — is the rejection tested? |
| Error path | For every success path, is the corresponding failure path tested? |
| Idempotency | If the operation can be called twice, is that safe? Is it tested? |
| Order sensitivity | Does the result depend on call order? Is that documented and tested? |
| Concurrent access | If the code will be called from multiple threads/tasks, is that safe? Is it tested? (Only if relevant.) |

Flag missing scenarios. Not every category applies to every change — exercise judgment, but don't skip a category without a reason.

---

## Check 4 — Test philosophy (Kent Dodds Testing Trophy)

For each test in the staged diff, check against the following rules. A violation is a finding.

**Behavior over implementation**
- Does the test name describe a behavior ("rejects an out-of-range choice index with StoryChoiceRangeError") or an implementation detail ("calls ChooseChoiceIndex with the given index")?
- Does the test assert on the *observable result* or on *how the result was produced*?

**Public API only**
- Does the test access private fields, `_inner` objects, unexported functions, or internal state? → violation
- Does the test mock types it owns (its own classes, its own modules)? → violation
- Does it mock only at genuine external boundaries (network, disk, clock, OS process, third-party API)? → ✓

**Real collaborators where cheap**
- Is anything mocked that could be a real instance without significant cost? → flag
- Does the test spin up a real `Story`, `Session`, `Player` etc. rather than a mock? → ✓

**Refactor-proof**
- Would this test break if you renamed an internal method while keeping the public contract identical? → violation
- Would it break if you changed the internal data structure while keeping the return value identical? → violation

**Testing Trophy shape**
- Does the commit add more unit tests than integration tests for behavior that crosses multiple units? → flag
- Is anything tested only at E2E level that could be tested cheaper at integration level? → flag
- Does any test reach for a snapshot that will be rubber-stamped on update? → flag

**Test names**
- `it("works")`, `it("test 1")`, `it("should work correctly")`, `it("handles the case")` → violation
- `it("rejects a negative index with StoryChoiceRangeError carrying attempted=−1")` → ✓

---

## Check 5 — SOLID violations

Scan the staged diff (new and modified source files only — not tests) for these patterns:

**Single Responsibility**
- Does any new class or module have more than one reason to change? Look for: a class that both validates *and* persists, a module that both formats *and* dispatches.
- Flag if a class's methods cluster into two distinct concern groups.

**Open/Closed**
- Does the new code require callers to modify existing files to add a new variant? A `switch` or `if/else if` chain on a type tag in the caller is often the smell.
- Flag if extensibility requires modification of existing classes rather than addition of new ones.

**Liskov**
- Does any new subtype throw where its base doesn't? Does it silently ignore a method the base defines?
- Flag if a subtype's contract is narrower than the base type's.

**Interface Segregation**
- Does any new interface force its implementors to define methods they don't use? A `Player` that must implement `selectChoice` *and* `persistToDatabase` is segregated wrong.
- Flag fat interfaces.

**Dependency Inversion**
- Does new code `new` a concrete dependency inside a class rather than receiving it? A class that constructs its own `LLMPlayer` internally cannot be tested without that player.
- Flag hardcoded `new ConcreteType()` inside class bodies where an abstraction or injection would be natural.

---

## Check 6 — Clean Code violations

Scan the staged diff for:

| Issue | What to look for |
|---|---|
| Magic values | Bare literals with semantic meaning: `if (index >= 99)`, `setTimeout(fn, 3000)`, `"choice:made"` string repeated in 4 files. Every meaningful literal should be a named constant. |
| Function does more than one thing | A function that "validates input, then transforms it, then persists it" is three functions. If "and" is required to describe what it does, split it. |
| Unqualified generic names | `data`, `info`, `result`, `value`, `temp`, `manager`, `handler`, `helper` without qualification. These carry no meaning at a call site. |
| What-comments | `// increment the index` above `index++`. Comments that restate the code add noise and rot. Only keep *why* comments: hidden constraints, workarounds for specific bugs, non-obvious invariants. |
| Half-finished surfaces | Any exported symbol with `TODO`, a stub body `{ return null; }`, or a comment that says "implement later". These must be complete or removed before commit. |
| Long parameter lists | More than 3–4 positional parameters is a smell — group into an options object. |

---

## Output format

Use this format so the user can scan it in 10 seconds:

```
Implementation review — [commit subject or staged file summary]

Check 1 · Plan gaps
  ✓ All phase items present  |  ✗ Gap: [item] — [present/partial/absent]

Check 2 · Use-case coverage
  ✓ All use cases covered  |  ✗ [use case] — no test / no implementation

Check 3 · Missing test scenarios
  ✓ Scenarios complete  |  ⚠ [behavior]: missing [scenario type]

Check 4 · Test philosophy
  ✓ Tests pass philosophy check  |  ✗ [test name]: [violation]

Check 5 · SOLID
  ✓ No violations  |  ✗ [file:line]: [principle] — [finding]

Check 6 · Clean Code
  ✓ No violations  |  ✗ [file:line]: [issue]

Summary: [N findings — fix before committing / Clean — proceed]
```

If a finding is **blocking** (plan gap, philosophy violation on a public API test, SOLID violation that breaks extensibility), say so and fix it before committing unless the user explicitly overrides.

If a finding is **advisory** (a test name that could be clearer, a function that's slightly long), surface it but don't block.

---

## Commit-flow position

```
[code changes complete]
     ↓
/staleness-audit    ← docs drift, TSDoc, export sync, stale markers
     ↓
/implementation-review   ← THIS SKILL
     ↓
git commit
     ↓
/release-check      ← is a release due?
```

---

## Anti-patterns

- Don't skip a check because "the change is small" — that's when violations sneak through.
- Don't invent a plan if none is findable — skip Checks 1–2 and say so.
- Don't treat every advisory finding as blocking — use judgment.
- Don't run test philosophy checks on non-test files, or SOLID checks on test files.
- Don't report "✓ clean" without actually reading the diff.
