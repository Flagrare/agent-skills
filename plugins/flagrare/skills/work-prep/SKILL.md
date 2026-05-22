---
name: work-prep
description: "Orchestrates the full preparation workflow for a ticket. Calls /flagrare:intake to gather context from Jira/Notion/Figma and resolve ambiguities, then calls /flagrare:atdd-plan to explore the codebase and produce a TDD-first implementation plan. Use when the user shares a ticket key (e.g. SKU-123), says 'start work on', 'pick up ticket', 'plan this feature', 'work prep', or provides a Jira URL."
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
4. Synthesise a context brief
5. Ask targeted clarifying questions
6. Resolve open questions with the user

**Wait for `/flagrare:intake` to complete before proceeding.** The context brief must be finalized and open questions resolved.

### Step 2: Invoke `/flagrare:atdd-plan`

Once `/flagrare:intake` has produced a complete context brief, invoke `/flagrare:atdd-plan`. Pass the context brief as opening context. This skill will:

1. Explore the codebase via `/flagrare:codebase-explore` to understand conventions and reusable pieces
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

---

## Flow position

```
/flagrare:work-prep [ticket ID or URL]
     |
     v
/flagrare:intake          <- context gathering, reference following, clarifying questions
     |
     v
/flagrare:atdd-plan       <- codebase exploration via /flagrare:codebase-explore, then ATDD-first plan
     |
     v
[user reviews plan]
     |
     v
[implementation begins]
```
