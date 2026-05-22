---
name: work-prep
description: "Orchestrates the full preparation workflow for a ticket. Calls /flagrare:intake (which gathers context from Jira/Notion/Figma, grounds the brief in the codebase via /flagrare:codebase-explore, then asks codebase-informed clarifying questions), then hands the codebase-grounded brief to /flagrare:atdd-plan for a TDD-first implementation plan. Use when the user shares a ticket key (e.g. SKU-123), says 'start work on', 'pick up ticket', 'plan this feature', 'work prep', or provides a Jira URL."
---

# Work Prep

Full preparation workflow: ticket context gathering followed by implementation planning.

This skill orchestrates two existing skills in sequence. It does not duplicate their logic.

---

## When to Use

- User shares a ticket key (e.g. `SKU-123`, `ST-456`, `CORE-789`)
- User provides a Jira/Atlassian URL
- User says "start work on", "pick up ticket", "plan this feature", "work prep", "let's work on [ticket]"
- User pastes a ticket key with no other context

---

## Workflow

### Step 1: Invoke `/flagrare:intake`

Call `/flagrare:intake` with the ticket reference. This skill will:

1. Parse the ticket ID/URL and identify the platform
2. Read the full ticket via MCP (Jira, Linear, etc.)
3. Follow all referenced links in parallel (Notion, Figma, Confluence, GitHub, etc.)
4. Synthesise a context brief (without questions yet)
5. **Ground the brief in the codebase** via `/flagrare:codebase-explore` — finding the files, utilities, and prior attempts the plan will touch
6. Ask **codebase-informed** clarifying questions (specific: "extend `src/x.ts` or fork it?" — not abstract: "where should this live?")
7. Resolve open questions with the user

**Wait for `/flagrare:intake` to complete before proceeding.** The context brief must be finalized, codebase findings populated, and open questions resolved.

### Step 2: Invoke `/flagrare:atdd-plan`

Once `/flagrare:intake` has produced a complete, codebase-grounded context brief, invoke `/flagrare:atdd-plan`. Pass the brief as opening context. This skill will:

1. Run its own `/flagrare:codebase-explore` pass (atdd-plan stays self-sufficient — intake's findings in the brief are additional input, not a substitute)
2. Produce an ATDD-first implementation plan with acceptance tests, named design patterns, SOLID audit, and gap review
3. Present the plan for user review

### Step 3: Confirm readiness

After the plan is presented:

> Plan complete. Review it and let me know if you want to adjust anything, or say "go" to start implementation.

---

## Anti-patterns

- Don't skip `/flagrare:intake` and jump to planning. Context gaps turn into rework.
- Don't invoke `/flagrare:atdd-plan` before clarifying questions are resolved.
- Don't start implementation before the plan is reviewed and approved.
- Don't re-fetch context that `/flagrare:intake` already gathered. Pass the brief forward.
- Don't ask clarifying questions before codebase grounding. Questions asked without knowing what exists are abstract and frequently miss the real ambiguity. intake handles this by calling `/flagrare:codebase-explore` before Step 5.
- Don't be surprised that `/flagrare:codebase-explore` runs twice in this flow — once in intake (scoped to inform questions) and once in atdd-plan (scoped to anchor the plan). atdd-plan stays standalone-callable; that requires it to do its own pass.

---

## Flow position

```
/flagrare:work-prep [ticket ID or URL]
     |
     v
/flagrare:intake          <- 1. read ticket + follow references in parallel
                             2. synthesise brief (no questions yet)
                             3. /flagrare:codebase-explore  <- ground brief in code
                             4. ask codebase-informed clarifying questions
                             5. resolve, finalize brief
     |
     v
/flagrare:atdd-plan       <- runs its own /flagrare:codebase-explore pass
                             (stays self-sufficient for standalone use),
                             then produces ATDD-first plan
     |
     v
[user reviews plan]
     |
     v
[implementation begins]
```
