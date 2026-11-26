---
name: atdd-plan
description: "Produce an ATDD-first implementation plan in Claude Code's native plan mode, with named design patterns called out where they earn their keep. The skill enters plan mode automatically (via the EnterPlanMode tool), runs /flagrare:codebase-explore to ground the plan in the actual codebase, then produces a plan-mode plan that MUST include all three: (1) 3-5 acceptance tests in plain English defining 'done' before any implementation, written behavior-first against the public API only; (2) any non-trivial structural decisions named as design patterns with a one-line rationale; and (3) the cheap SOLID and Clean Code wins in the code it extends (a rule kept in two places by hand, parallel maps, a sibling that does it better), planned inline instead of copying the local pattern's weakness. Plan mode's native approve/edit/reject button UI is the close, ExitPlanMode is how the skill ends. Use whenever the user wants to plan a feature, fix, or refactor, 'how should we implement X', 'plan this', 'let's design X', 'where do we start on Y'. Tests follow Kent Dodds Testing Trophy: behavior over implementation, integration-heavy, public-API-only, refactor-proof. The skill stops at the plan; it does not write implementation code."
---

# ATDD Plan

This skill produces an implementation plan in **Claude Code's native plan mode**. It does not reinvent plan mode's output shape, Claude already knows how to write a plan-mode plan. The skill exists to enforce three things plan mode alone won't:

1. **Plan mode is actually used**: `EnterPlanMode` at skill start, `ExitPlanMode` at skill end. The user gets the native approve/edit/reject button UI, not a wall of markdown.
2. **The plan is grounded in the real codebase**: `/flagrare:codebase-explore` runs before any planning, so the plan references the actual files, conventions, and reusable pieces that exist.
3. **The plan contains the three non-negotiables below.**

Everything else about the plan's form, length, section ordering, tone, follows plan mode's defaults. Don't impose extra structure on top.

**REQUIRED BACKGROUND:** Invoke `/flagrare:testing-philosophy` before writing the Acceptance Tests. It defines, layer-agnostically, what a good test is, behavior over implementation, the Testing Trophy, and the e2e necessity floor below. The AT rules here are its application to planning; read both.

---

## The three non-negotiables

Every plan this skill produces **must include** all three:

### 1. Acceptance Tests (ATDD)

3 to 5 acceptance tests, written in plain English, that define "done" before implementation begins. Each test must:

- **Exercise the public API only**: no private methods, no internal state, no `_inner` fields. A test that breaks on a behavior-preserving rename is a broken test, not a broken refactor. (Apply the acid test from `/flagrare:testing-philosophy`: would this break under a behavior-preserving refactor? Does it assert what a real user observes?)
- **Describe behavior, not method names**: `"returns an empty Scene when the story has ended"` not `"test_advance_flag"`. A name that describes a mechanism (`"calls advanceFlag"`) is the tell of an implementation-detail test.
- **Use real collaborators where cheap; mock only at external/network/clock/process/OS boundaries.** Never assert on spy/mock call-counts for a collaborator you own, that asserts the mechanism, not the behavior.
- **Follow the Testing Trophy**: integration-heavy is the default, because most regressions live between units, not inside them. Unit tests are reserved for pure functions with complex logic.
- **Include the e2e floor for user-facing work**: if the feature is user-facing, at least one AT must exercise the critical happy path end-to-end through the real, assembled system (browser journey for a UI; running-service-over-HTTP-against-a-real-DB for a backend; subprocess for a CLI; public-API-as-a-consumer for a library). "Mostly integration" is not "skip e2e": one or two critical paths, not one per scenario, but never zero for a user-facing feature.

Write 3-5 ATs. Too few leaves behavior undefined; too many creates a brittle harness.

### 2. Design Patterns (named, with rationale)

For every **non-trivial structural decision**, name the pattern and give a one-line rationale that explains why it fits *this* problem, not what the pattern is in the abstract.

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

Only name a pattern when it genuinely solves the stated problem. Forcing a pattern where it doesn't fit is worse than no pattern. If a plan's structural decisions are all trivial (one obvious file change, no abstraction needed), say so explicitly, *"No design patterns needed; this is a single-function fix in `path/to/file`"*, rather than inventing one.

### 3. Easy wins over copied weaknesses

Following the codebase's patterns is the default, not a reason to copy their flaws. When the code the plan extends has a weakness that SOLID or Clean Code would name, and fixing it is cheap, the plan fixes it as part of the change. Look for these in what exploration found:

- **A rule kept in two places by hand.** A list, map or constant copied from another source of truth (route config, a schema, an enum elsewhere) drifts the day someone changes the original. Derive it from the source, or keep both halves in one structure, or add a test that fails when they disagree.
- **Parallel structures keyed by the same thing.** Two maps from the same type to different facts (`TYPE → url` and `TYPE → access rule`) belong in one map of objects (`TYPE → { url, rule }`), so adding a type means filling one entry, not remembering two.
- **A sibling that already does it better.** When two places in the codebase solve the same problem differently, follow the sounder one, even if it is not the closest one. Say which you picked and why.
- **Magic values, unnamed conditions, a function doing two things** in the code the change touches.

A win is easy when it stays in the files the change already touches (or one hop from them), changes no public contract, adds no dependency and needs no edits to unrelated callers. Plan those inline, one line each, in the step where they happen: *"The URL map becomes `{ href, rule }` per type, like the menu config next to it, so a card's link and access rule can't drift apart."* Bigger improvements get one line under a "Follow-ups" note and are not done in this change.

If exploration found nothing worth improving, say so in one line. Field-tested the hard way: a plan added a hand-written map from each card type to its page's access rule, next to an existing map of the same types to their links. A sibling menu config in the same codebase already kept link and rule together. The reviewer had to point out that nothing kept the new map in sync with the routes, and the user asked why the plan had not done it that way from the start.

---

## Procedure

### Step 1: Enter plan mode

Call `EnterPlanMode` immediately. Do not preface with a summary or ask for confirmation first, the user invoked a planning skill, plan mode is the right posture, just enter it. Plan mode restricts the session to read-only tools, which is exactly what planning needs.

If `EnterPlanMode`'s schema isn't loaded, use `ToolSearch` with `select:EnterPlanMode,ExitPlanMode` to load both before proceeding.

### Step 2: Explore the codebase

Invoke `/flagrare:codebase-explore`. Pass it the user's description (or the brief from `/flagrare:intake` if the skill was chained through `/flagrare:work-prep`).

**Hard requirement: invoke the skill, not a substitute.** Do not replace it with a generic `Explore` agent or manual grep, the skill encodes a specific methodology (prior-branch discovery, convention mapping, utility inventory, dependency tracing) and produces structured findings the plan depends on.

Wait for it to complete. Do not start writing the plan until you have its output.

### Step 3: Confirm scope (lightweight gate)

Before writing the plan, post a 3-5 sentence synthesis of what you understood:

- One-sentence framing of the feature/fix/refactor
- The 2-3 most relevant locations exploration surfaced (with `path/to/file.ts:42`-style references)
- 1-2 explicit assumptions you're planning around

Then call `AskUserQuestion` with three options:

- **Looks right, write the plan** (Recommended)
- **I want to adjust direction first**: user describes the adjustment, you re-run Step 3
- **Different direction entirely**: user provides new framing, you may need to re-run Step 2

This gate is light by design, it's one button click when the synthesis is correct, which is the common case. Its purpose is to prevent committing to a wrong direction before producing a full plan, not to interrogate the user.

### Step 4: Write the plan

Write a plan-mode plan. Follow Claude Code's normal plan-mode conventions for shape, length, and tone, narrative + targeted lists, scannable, no padding.

**Requirements layered on top of plan mode's defaults (the fourth only when a bet is present):**

1. Include the **Acceptance Tests** section described above (3-5 ATs).
2. **Name the design patterns** for any non-trivial structural decisions, with one-line rationale each. Or explicitly state none are needed.
3. **Plan the easy wins** from non-negotiable 3 inline, in the step they belong to, and list bigger improvements as follow-ups. Or say in one line that the code being extended has none.
4. When the opening context carries a bet from `/flagrare:measure-impact` whose tracking does not exist yet, add the event or metric as an early step and one acceptance test that it records the change. Without a bet, add nothing.

**Do NOT add**:

- A separate SOLID audit section (SOLID and Clean Code shape the steps themselves, through the easy wins)
- A separate Clean Code checklist
- An enumerated Gap Review by category (empty/boundary/error/concurrent/state-machine/hostile/ordering)
- A Design Patterns table separate from the prose
- A Refactor Pass Reminder
- An Implementation Phases section with builds/gates/patterns columns

Those were artifacts of an older form that produced deliverable documents. Plan mode plans don't need them, they make the plan long without making it better. If something genuinely matters to the design (a real concurrency risk, a real boundary issue), call it out inline in the prose where it lives. A plan that surfaces 2-3 *specific* risks based on what exploration found is far more useful than one that enumerates every theoretical category.

### Step 5: Exit plan mode

Call `ExitPlanMode` with the plan as the `plan` argument. This gives the user the native button-driven approve/edit/reject UI, which is what they invoked the skill to get.

Do not follow `ExitPlanMode` with a prose question or summary. The button UI is the close.

---

## Anti-patterns: refuse these

- **Acceptance tests that assert on internal state** (`_inner`, mock call counts on types you own, private fields). Refactor-proof or it's not an AT.
- **Pattern names with no rationale**: "we'll use a Strategy" with no explanation of what it replaces or why this problem needs one.
- **A SOLID / Clean Code / Gap Review / Phases section** in the plan output. Those were the old form; plan mode does not need them.
- **Skipping `EnterPlanMode`** and producing a markdown plan in the regular conversation. The user wants the native plan-mode UX; that means the actual tool, not an approximation.
- **Skipping `/flagrare:codebase-explore`.** The plan must be grounded in the real codebase; references to actual `path/to/file.ts:42` locations are what separate this from a generic chatbot plan.
- **Coverage targets as a goal.** Coverage is a side effect of testing the right behaviors, not something the plan aims at.
- **A user-facing feature whose ATs never prove the layers connect.** Unit + integration coverage with no e2e/full-stack happy-path test is a gap, even when it looks complete. The e2e floor is non-optional for user-facing work, see `/flagrare:testing-philosophy`.
- **Copying a pattern's weakness because it is the local pattern.** "The existing map only has URLs, so I added a second map" is how a hand-kept duplicate ships. Check the pattern against SOLID and Clean Code before extending it, and take the cheap fix.
- **Closing with a prose question after `ExitPlanMode`.** The button UI is the close. Don't double-prompt.
