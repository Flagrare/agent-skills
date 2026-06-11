# Research: Claude Code `/goal` as an anti-stall mechanism for multi-step skills

- **Slug:** `2026-06-11-claude-code-goal-anti-stall`
- **Date:** 2026-06-11
- **Status:** complete
- **Triggered by:** Diagnosing why `/flagrare:work-prep` / `/flagrare:intake` frequently stop after emitting the context brief and before asking clarifying questions. Evaluating whether `/goal` is the right structural fix.
- **Informed:** [`/flagrare:intake` SKILL.md](../../plugins/flagrare/skills/intake/SKILL.md) (added "Lock the goal first" step + brief-seam no-yield notes) and [`/flagrare:work-prep` SKILL.md](../../plugins/flagrare/skills/work-prep/SKILL.md) (added Step 0 session-spanning goal).

## Question

When a skill drives a long, multi-step workflow, the model often emits a large prose artifact (a "context brief") and then ends its turn instead of continuing through the remaining steps. Is Claude Code's `/goal` command an officially supported, durable mechanism for keeping the model working across turns until an explicit exit condition is met, and if so, what are the constraints that should shape how a skill writes the goal condition? Specifically: does it survive context compaction, how does the evaluator decide "done," and can it be used safely inside nested skill invocations?

## Sources

### [Keep Claude working toward a goal](https://code.claude.com/docs/en/goal)
- **Authors / Org:** Anthropic (official Claude Code documentation)
- **Type:** vendor doc
- **Published:** ongoing (feature requires Claude Code v2.1.139+)
- **Accessed:** 2026-06-11
- **Relevance:** high
- **What this contributed:** The primary and authoritative description of `/goal`. Confirms the feature is GA, defines its mechanism (a session-scoped prompt-based Stop hook plus a fresh-model evaluator that runs after every turn), and states the constraints that determine how a skill must phrase a goal condition. This is the source the whole recommendation rests on.
- **Quoted:**
  > "The `/goal` command sets a completion condition and Claude keeps working toward it without you prompting each step. After each turn, a small fast model checks whether the condition holds. If not, Claude starts another turn instead of returning control to you. The goal clears automatically once the condition is met."

  > "The evaluator judges your condition against what Claude has surfaced in the conversation. It doesn't run commands or read files independently, so write the condition as something Claude's own output can demonstrate."

  > "`/goal` is a wrapper around a session-scoped prompt-based Stop hook. Each time Claude finishes a turn, the condition and the conversation so far are sent to your configured small fast model, which defaults to Haiku. The model returns a yes-or-no decision and a short reason."

  > "One goal can be active per session. ... If a goal is already active, the new one replaces it."

  > "`/goal` runs only in workspaces where you have accepted the trust dialog, because the evaluator is part of the hooks system. `/goal` is also unavailable when `disableAllHooks` is set at any settings level or when `allowManagedHooksOnly` is set in managed settings."

### [Commands / Slash commands: Claude Code Docs](https://code.claude.com/docs/en/slash-commands)
- **Authors / Org:** Anthropic (official Claude Code documentation)
- **Type:** vendor doc
- **Published:** ongoing
- **Accessed:** 2026-06-11
- **Relevance:** low
- **What this contributed:** Corroborated that `/goal` is a first-class slash command in the official command set (it surfaced in the official slash-command listing during the search), distinguishing it from an emergent/undocumented convention. No independent design detail beyond the dedicated `/goal` page.

## Synthesis

**`/goal` is official, GA, and purpose-built for exactly this failure mode.** It requires Claude Code v2.1.139+. Setting a goal makes the model keep working across turns until a separate evaluator confirms an explicit completion condition. One of Anthropic's own listed use cases is "Implementing a design doc until all acceptance criteria hold", structurally identical to a planning/intake workflow that must run to a defined end state rather than stopping after a report.

**Mechanism.** `/goal` is a wrapper around a session-scoped prompt-based Stop hook. After every turn, the condition plus the conversation so far is sent to the small fast model (Haiku by default), which returns yes/no + a one-line reason. "No" tells the model to keep working, passing the reason as guidance for the next turn; "yes" clears the goal. This is harness state, not message-history state, which is why it is a categorically stronger forcing function than prose reminders ("don't stop here") that live in the skill body and only bias the acting model.

**The load-bearing design constraint:** the evaluator *does not call tools and does not read files*, it can only judge what the acting model has already surfaced in the conversation. Therefore a goal condition must be written as something the model's own output can demonstrate. For an intake/planning skill this means the condition should reference observable conversational events, e.g. "clarifying questions have been asked via the AskUserQuestion tool and answered, and `/flagrare:atdd-plan` has been invoked (or the user explicitly chose Stop)", not an internal state the evaluator cannot see. Conditions can be up to 4,000 characters and may include a bound such as "or stop after N turns."

**Two constraints that matter for nested skills:**

1. **One goal per session; a new goal replaces the active one.** In the `work-prep → intake → atdd-plan` chain, only a single goal can be live. The orchestrator that is the entry point should own the goal: `work-prep` should set a goal spanning the whole `intake → atdd-plan → confirm` sequence, and `intake` should *skip* setting its own goal when it detects the existing `[work-prep]` prefix, otherwise the inner goal silently overwrites the outer one.
2. **Requirements / availability.** `/goal` only works in trusted workspaces and is disabled when `disableAllHooks` or `allowManagedHooksOnly` is set, because it is part of the hooks system. A skill relying on it should degrade gracefully (fall back to the prose anti-stall guidance) rather than assume it is always available.

**Compaction caveat (not fully documented, flagged honestly).** The official page does not state whether a goal survives context compaction. What it *does* say: the goal is session-scoped hook state and is restored on `--resume`/`--continue` (with timers/counters reset). Inference, not documented fact: because the goal lives in the hook system rather than the transcript, the *goal itself* is robust to compaction, but the *evidence the evaluator reads* is "the conversation so far," which compaction can truncate. Practical consequence: write conditions whose satisfying evidence is re-demonstrable in recent output, and do not treat `/goal` as an absolute lock.

**Bottom line.** Anchoring the intake/work-prep anti-stall fix on `/goal` is supported by official documentation and matches a documented use case. It should be the primary mechanism, set at the very top of the entry-point skill (before any large artifact is emitted), paired with: (a) a TodoWrite coverage ledger, (b) immediate same-turn skill-to-skill handoff to remove prose gaps, and (c) the existing prose seam notes as defense-in-depth for environments where hooks (and thus `/goal`) are unavailable. The internal flagrare skills `ux-audit`, `figma-matcher`, `debug-hunt`, and `smoke-test` already use this pattern for the same reason; this research confirms it is officially grounded rather than folklore.

## Downstream uses

- `/flagrare:intake` SKILL.md, "Lock the goal first" pre-flight step with a conversation-demonstrable condition; skips when the `[work-prep]` prefix is present; plus Open-Questions-are-internal and no-yield-at-the-brief-seam notes as hooks-disabled fallback.
- `/flagrare:work-prep` SKILL.md, Step 0 sets a session-spanning `/goal` covering `intake → atdd-plan → confirm`; intake skips its own goal under the prefix to respect the one-goal-per-session limit.
- Pending sweep: all remaining flagrare skills audited for the same multi-step-stall pattern (tracked separately).
