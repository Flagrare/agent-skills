---
name: atdd-plan
description: "Produce an ATDD-first implementation plan with named design patterns, SOLID audit, and gap review. Use whenever the user wants to plan a feature, fix, or refactor — 'how should we implement X', 'plan this', 'let's design X', 'where do we start on Y'. Tests follow Kent Dodds Testing Trophy: behavior over implementation, integration-heavy, public-API-only, refactor-proof. Never start writing implementation until the plan is agreed and the acceptance tests are defined."
---

# Plan

Produce a structured ATDD-first implementation plan. Acceptance tests define "done" before a single line of implementation exists. Design patterns are named and justified. SOLID is audited. The gap review is never empty.

---

## Step 1 — Explore the codebase via `/flagrare:codebase-explore`

Before writing the plan, invoke `/flagrare:codebase-explore`. Pass it the context brief (from `/flagrare:intake`) or the user's description. It will:

1. Check existing branches and PRs for prior attempts
2. Explore relevant source files to understand conventions and reusable pieces
3. Map dependencies, data flows, and integration points
4. Inventory reusable utilities and shared components

Wait for `/flagrare:codebase-explore` to complete. Use its findings to inform every subsequent step. Do NOT write acceptance tests or implementation phases until you have the exploration output.

---

## Step 2 — Understand before planning

Before writing anything, answer:
- What is the feature/fix/refactor in one sentence?
- Who calls it and what do they observe when it works?
- What are the hard failure modes?

If the feature is ambiguous, ask. Planning a misunderstood requirement is worse than not planning.

---

## Step 3 — Acceptance Tests (written before implementation)

Each AT must:
- Exercise the **public API only** — no private methods, no internal state, no `_inner` fields
- Describe behavior in English: `"returns an empty Scene when the story has ended"` not `"test_advance_flag"`
- Use **real collaborators** where cheap; mock only at external/network/clock/process/OS boundaries
- Be **refactor-proof**: a test that breaks on a behavior-preserving rename is a broken test, not a broken refactor
- Be written **and run to observe the failure** before any implementation begins — a test that passes on first run is a smell

### Testing Trophy (this is the shape, not a guideline to ignore)

```
         /‾‾‾‾‾‾‾\
        /  E2E (few) \
       /‾‾‾‾‾‾‾‾‾‾‾‾‾\
      / Integration    \   ← the bulk; most bugs hide between units
     /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
    /   Unit (targeted)  \
   /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
  /   Static (types/lint)  \  ← free, catches the most bugs per dollar
 /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
```

Integration tests are the bulk. Most regressions live between units, not inside them. Unit tests are reserved for pure functions with complex logic (quantization, scoring math, parsers). E2E tests are expensive — one or two per critical path, not one per scenario.

Write 3–7 ATs per feature. Too few leaves behavior undefined. Too many creates a brittle harness.

---

## Step 4 — Name the design patterns

Don't ad-hoc the structure. For every significant architectural decision, name the pattern and explain why it fits this specific problem — not just what the pattern is.

| Problem shape | Pattern to consider |
|---|---|
| Swap implementations without changing callers | Strategy |
| Hide a complex subsystem behind a simple interface | Facade |
| Decouple data access from business logic | Repository |
| Notify dependents without coupling to them | Observer |
| Add behavior without changing the object | Decorator |
| Create objects without specifying the class | Factory / Abstract Factory |
| One algorithm, pluggable steps | Template Method |
| Encapsulate a request as an object | Command |
| Wrap incompatible interfaces | Adapter |
| One instance shared across the system | Singleton (use sparingly) |

Forcing a pattern where it does not fit is worse than no pattern. Only name it when it genuinely solves the stated problem.

---

## Step 5 — SOLID audit

For each principle, one sentence on how the design honors it — or documents a conscious tradeoff:

- **S** — Single Responsibility: each class/module has one reason to change
- **O** — Open/Closed: extend behavior without modifying existing code
- **L** — Liskov: every subtype is fully substitutable for its base type
- **I** — Interface Segregation: no client forced to depend on an interface it doesn't use
- **D** — Dependency Inversion: depend on abstractions, not concretions

A documented tradeoff ("S is softened here because X justifies it") is acceptable. An unexamined violation is not.

---

## Step 6 — Clean Code checklist

Apply these before calling any phase complete:

- No magic values — every meaningful literal is a named constant
- Functions do one thing — if "and" is needed to describe it, split it
- Names are self-documenting — no `data`, `info`, `manager`, `handler` without qualification
- Comments explain *why*, never *what* — the code already says what; only write a comment for a non-obvious invariant, a workaround for a specific bug, or a hidden constraint
- No half-finished implementations — every public surface is complete, or explicitly behind a flag

---

## Step 7 — Implementation phases

Order phases so each one can be merged independently. Each phase must include:

- What gets built
- Which ATs gate this phase (must pass before moving on)
- Which patterns are introduced or extended

A phase that can't stand alone without a follow-up is too large.

---

## Step 8 — Gap review (never empty)

Before declaring the plan done, work through:

- What happens on empty / nil / zero input?
- What happens at the boundary (first item, last item, exactly one item)?
- What is the error path for every success path?
- Are there concurrent access concerns?
- Is there a state machine? Are all transitions covered, including invalid ones?
- What does a hostile or careless caller do to break this?
- Are there any implicit ordering assumptions that need to be enforced?

An empty gap review means you did not look.

---

## Output format

Always produce the plan in this exact structure:

```
## [Feature / fix in one sentence]

## Acceptance Tests
1. `describe("X") > it("Y")` — [what makes this pass]
2. …

## Design Patterns
| Problem | Pattern | Rationale |
|---|---|---|

## Implementation Phases
### Phase 1 — [name]
- Builds: …
- Gates: AT #1, #2
- Patterns introduced: …

### Phase 2 — [name]
…

## SOLID Audit
- S: …
- O: …
- L: …
- I: …
- D: …

## Gap Review
- …

## Refactor Pass Reminder
No phase is complete until naming, duplication, structure, and SOLID adherence have been reviewed.
```

---

## Anti-patterns — refuse these

- ATs that assert on internal state (`_inner`, mock call counts on types you own, private fields)
- Phase ordering that puts implementation before acceptance tests
- Pattern names with no rationale ("we'll use a Strategy" with no explanation of what it replaces or why)
- An empty gap review
- Coverage targets stated as a goal — coverage is a side effect of testing the right behaviors
