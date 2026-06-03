# Tutor: Socratic Tutoring Mode

**Date:** 2026-05-28
**Status:** Approved (pending implementation plan)
**Affected skill:** `plugins/flagrare/skills/tutor/SKILL.md` (new)

## Why

There's no on-demand "teach me how to do this, don't do it for me" mode in the flagrare skill set today. The closest existing prior art — the Anthropic Learning and Explanatory output-style plugins — runs *always-on* via SessionStart hooks, which means it pays a token tax on every session and can't be scoped to a topic, file, or single decision point. A skill is a better fit: invoked explicitly, scoped per call, exits cleanly.

The reference implementation we modelled against is **Boots** (boot.dev's AI tutor). The full research catalog with sources and credit lives at [`docs/research/2026-05-28-boots-ai-tutor-design.md`](../research/2026-05-28-boots-ai-tutor-design.md); three findings from it are load-bearing for this spec:

1. The Socratic posture is held by the prompt, nothing else — Sonnet/Opus will leak the answer unless explicitly and repeatedly told not to.
2. Context curation beats context volume — Boots's team found that injecting 100k tokens of lesson history *hurt* quality vs. a small curated slice.
3. Negative examples in the prompt beat abstract rules — Boots's iteration loop is "Discord complaint → one-sentence negative example → prompt."

This skill applies all three.

## Skill identity

- **Name**: `/flagrare:tutor`
- **File**: `plugins/flagrare/skills/tutor/SKILL.md`
- **Architecture**: Single SKILL.md (~250 lines), runtime router into three scope branches that converge into one shared Socratic engine.

### Trigger surface

**Explicit-intent only.** Colloquial phrases like `teach me X`, `explain this`, `walk me through this` are *excluded* — users mean those when they want a quick answer, not a 20-turn dialogue.

Triggers:
- `tutor me on X` / `tutor me through X`
- `tutor mode`
- `be my tutor` / `act as a tutor`
- `Socratic me` / `use the Socratic method`
- `use the tutor skill` / `/flagrare:tutor`
- `I don't want the answer, I want to understand`

The SKILL.md frontmatter `description` includes an explicit DOES-NOT-TRIGGER negative-example line to prevent auto-fire on colloquial near-matches. This is the same pattern Lane Wagner described for in-skill behavior, applied to the skill-routing surface.

## Mode entry

On invocation, the skill runs three checks in order, then enters one of three branches.

### Pre-entry: learning-path log check (per-repo, opt-in)

The skill checks for marker files in `.flagrare/` at the project root:

| Marker present | Behavior |
|---|---|
| `.flagrare/tutor-log.md` | Opt-in confirmed. Append session summary on close. |
| `.flagrare/tutor-log.disabled` | Opt-out confirmed. Don't log, don't ask. |
| Neither | First invocation in this repo. Ask the user (see below). |
| Non-project directory (see below) | Skip log entirely. Don't create `.flagrare/`. Don't ask. |

A directory counts as a **project directory** if any of these are present at or above the current path: a `.git/` directory, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `Gemfile`, `composer.json`, or `mix.exs`. Anything else is non-project — the skill runs without logging and never creates `.flagrare/` there.

First-invocation question (`AskUserQuestion`, 3 options):
- **Yes, log to `.flagrare/tutor-log.md`** — creates the file, appends future sessions
- **No, don't ask again** — creates `.flagrare/tutor-log.disabled` marker
- **Skip for now, ask next time** — neither marker created

When creating `tutor-log.md`, the skill prints: "Created `.flagrare/tutor-log.md`. Add to `.gitignore` if you want it personal." — but does **not** auto-modify `.gitignore`. User decides whether the log is personal or team-shared.

### Q1 — Scope (`AskUserQuestion`, 3 options)

- **In-context** — tutor against current focus (file/PR/function/error)
- **Topic** — tutor against a topic the user names
- **Instead-of-implementing** — tutor instead of building the thing Claude was about to build

### Q2 — Persona (`AskUserQuestion`, 3 options)

Ascending intensity. Persona affects voice only, not branch logic.

| Slot | Name | Voice |
|---|---|---|
| Low intensity | **Echo** | Calm, observational. Mirrors thinking back. Barely a character. |
| Mid intensity | **Cipher** | Knowing, slightly mysterious. Treats concepts as puzzles to crack. |
| High intensity | **Vex** | Pushy, leading, slightly antagonistic-but-caring. Frustration as curriculum. |

## Three scope branches

All three branches converge into the same Socratic engine. The differences are *only*: what context the branch loads, how it confirms scope, and how it phrases the opening question.

### Branch 1 — In-context

Skill identifies what's in current focus from the conversation state: most recently read file, current PR, last referenced function, last error. Confirms with the user via free-text:

> "Tutoring you against `src/auth/middleware.ts:handleSession()` — the function we were just looking at. Confirm scope, or name something different."

On confirmation (or rename) → opening turn.

### Branch 2 — Topic

Skill asks the user to name the topic with a specificity rule:

> "What topic? Be specific — 'React Suspense' or 'how async iterators work in Python' is good. 'JavaScript' is too broad and the session will go in circles."

If the topic intersects with the local codebase ("teach me how auth works here"), the skill optionally calls `/flagrare:codebase-explore` to ground itself. Otherwise, model knowledge only.

### Branch 3 — Instead-of-implementing

Skill scans the current conversation for what Claude was about to implement: an active plan, a TaskCreate list, an EnterPlanMode artifact, a recent "I'll build X" statement.

If candidates found: `AskUserQuestion` with auto-detected candidates as options, "Other" implicit for custom input.

If nothing detected: free-text question, "What should I be teaching you to build?"

Branch 3 makes a **stated promise** at entry: "My intended solution stays in my context. I won't show it." This is a prompt-level commitment in plain English — Claude is now visibly on the hook for the guardrail, which is a stronger constraint than an internal rule.

## Socratic engine

### Opening turn

After branch entry, the engine always opens with a posture statement + a calibration question:

> "OK — tutoring you against `[scope]`. I'm going to ask, not tell. Say **'stop tutoring'** whenever you want to exit. If you want me to just show you instead, say so. Let's start: **[opening question]**"

The opening question probes the user's existing mental model rather than starting fresh:

| Branch | Opening question shape |
|---|---|
| In-context | "Walk me through what you think this code is doing." |
| Topic | "What's your current understanding of `[topic]`?" |
| Instead-of-implementing | "How would you start? Don't write code yet — talk me through your approach." |

The "say so if you want me to just show you" line is the always-visible escape hatch.

### Turn loop

Every dialogue turn after the opening:

1. **Classify** the user's last response: `converging` / `partial` / `wrong-or-confused` / `stalled` / `reveal-requested`.
2. **Pick the move** for that state:

| State | Move | Shape |
|---|---|---|
| `converging` | Affirm + sharpen | Name what they got right with one specific phrase, then push one level deeper |
| `partial` | Redirect via question | Counterexample question that exposes the gap |
| `wrong-or-confused` | Scaffold down a rung | More basic preceding question |
| `stalled` | Increment counter; trigger stuck-offer at 3 consecutive | See below |
| `reveal-requested` | Enter reveal mode at user's chosen rung | See ladder below |

3. **Output exactly one question per turn.** No multi-question turns, no lectures, no code blocks during dialogue.

### Stuck-offer

On the 3rd consecutive stall, the engine breaks character briefly with an `AskUserQuestion` (3 options):

> "You've stalled three times. I can give you a sharper hint, or just show you — your call. Or keep going if you want another shot."

- `keep going` → reset stall counter, continue dialogue
- `sharper hint` → enter reveal mode at rung 1
- `show me` → enter reveal mode at rung 3

### Scaffolding ladder (reveal mode only)

| Rung | What's revealed | Example shape |
|---|---|---|
| 1 — Sharper hint | Concrete pointer to the right region | "Look at where `session` is initialized. What's the default?" |
| 2 — Near-reveal | Mechanism stated, application still asked | "`session` is `undefined` when the cookie's missing. So what does your check need?" |
| 3 — Full reveal | Answer + *why* + one verify-back question to close the topic locally | "It's `req.session?.userId ?? null`. The `?.` handles the undefined session, the `??` keeps the explicit-null contract. Quick check: what would `?.` do differently than `&&` here?" |

Reveal mode always exits with one verify-back question — even at rung 3 — to prevent passive consumption of the reveal. This is *not* the session close; it's a local check before the dialogue continues or the user invokes the close phrase.

## Negative examples (seed list)

Per the Boots research, this section is expected to grow from observed failures. Seed list of 10:

1. **Never reveal the answer** unless the user explicitly asked or accepted a stuck-offer.
2. **Never ask multiple questions in one turn.** One question, one focus.
3. **Never lecture.** Every dialogue-mode turn ends with a question.
4. **Never dump code blocks during dialogue mode.** Inline references like `req.session` are fine; full snippets aren't until reveal.
5. **Never use empty validators** like "Great question!" / "Good thinking!" — give one specific phrase or none.
6. **Never apologize for asking.** "Sorry to keep asking" is the strongest signal of a tutor about to fold and tell.
7. **Never falsely validate.** If the user got it wrong, the next move is a redirect question, not "yes, sort of, but…".
8. **Never repeat the same question after a stall.** Rephrase or scaffold down a rung.
9. **Never drift off-topic.** If the user asks something unrelated mid-session, redirect: "Park that — back to X."
10. **In Branch 3: never let the canonical solution into the turn.** It stays in Claude's context. The user has to produce their own version. The skill made a stated promise — breaking it is the worst failure mode.

## Close

**Explicit user action only.** No verify-back gate at session end.

The skill listens for any of: `stop tutoring`, `stop tutor`, `end tutor`, `exit tutor mode`, `we're done tutoring`, `close tutor`. On any of those, the skill exits cleanly. No comprehension check, no recap unless the user asks.

Trade-off accepted: users can exit thinking they understand when they don't. That risk is on the user, not on a flaky model-side gate. A model-side mastery check that fires unevenly is a worse failure mode than no check at all.

On exit, if logging is enabled (see Pre-entry), append a structured H2 entry to `.flagrare/tutor-log.md`:

```markdown
## 2026-05-28 — Branch 3 (instead-of-implementing) — Vex
**Topic**: `handleSessionTimeout()` design
**Covered**: optional chaining behavior with undefined sessions; the `?? null` vs `&& null` distinction
**Stuck on**: when session.userId is `0` vs `undefined` (1 stuck-offer accepted at rung 2)
**Reveal level reached**: rung 2 (near-reveal accepted, rung 3 not needed)
```

Each session is its own H2 — diffable, scannable, structured enough to be re-loaded as context by future sessions if a "resume / continue learning path" feature ships later.

## Cross-skill integration (deliberately minimal)

1. **Branch 2 → `/flagrare:codebase-explore`** (optional) — called when topic intersects local code.
2. **Branch 3 starting context** — pure read of current conversation. No skill call.
3. **At close: no automatic handoff.** Skill exits. No "smoke-test now?" / "ready for atdd-plan?" suggestions. User knows what they want next.

## Re-entry and interruption

Stateless across invocations. Re-invoking `/flagrare:tutor` mid-session is a **fresh start** — no resume of prior dialogue. Matches every other flagrare skill.

If the user is inside another flagrare skill (atdd-plan, intake, etc.) and invokes `/flagrare:tutor`, **tutor takes over.** No graceful resume of the prior skill. User can re-invoke the prior skill manually after.

The learning-path log is the only cross-session persistence in the design.

## AskUserQuestion inventory

Five fixed-option surfaces. Everything else is free-text dialogue (the Socratic engine itself never uses `AskUserQuestion` — that would silently destroy the pedagogy).

| # | Where | Options |
|---|---|---|
| 0 | First-invocation-in-repo logging question | yes / never / later |
| 1 | Entry Q1 — scope | in-context / topic / instead-of-implementing |
| 2 | Entry Q2 — persona | Echo / Cipher / Vex |
| 3 | Branch 3 task picker (when candidates detected) | auto-detected candidates + Other |
| 4 | Stuck-offer at 3 stalls | sharper hint / show me / keep going |

## Out of scope for v1

Explicit non-goals for the first version:

- **Session-start log resume** — reading prior log entries to offer "continue from last time." Log format is designed to support this, but the feature isn't shipping in v1.
- **Mode-aware pedagogy variants** — all three scope branches use the same Socratic engine. No branch-specific pedagogy adjustments.
- **Cross-skill auto-handoff at close** — no suggestions to invoke smoke-test, implementation-review, etc.
- **Verify-back close gate** — explicitly removed during design. Users exit with the close phrase.
- **Frustration sentiment detection beyond the stall counter** — no separate "user seems frustrated" classifier. Stall counter is the only frustration signal.
- **Multi-session topic threading** — each session is independent. The log is append-only context, not stateful threading.

## Failure modes to watch for

Things that will likely show up in real use and need negative-example additions:

- The tutor will probably try to *show* code in Branch 3 ("Here's roughly the shape: ...") even after the stated promise. Rule #10 is there to prevent this; it may need reinforcement.
- The tutor may collapse multi-turn dialogues into "let me just summarize..." paragraphs. Rule #3 covers this but the rule may need to be louder.
- The "one question per turn" rule will be tested when a concept genuinely has two prerequisites. The right move is to pick one and defer the other, but the model may try to chain.
- Branch 2 over-broad topics ("teach me JavaScript") will produce circular sessions. The opening prompt warns the user but the warning may need to be enforced ("Too broad. Narrow down or I'll pick a sub-topic.").

These are observation hypotheses, not guaranteed bugs. The negative-examples list is expected to grow as real failures appear.
