# Tutor Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `/flagrare:tutor`, an on-demand Socratic tutoring skill with three scope branches (in-context / topic / instead-of-implementing), three intensity-graded personas (Echo / Cipher / Vex), explicit-close-phrase exit, and per-repo opt-in learning-path logging to `.flagrare/tutor-log.md`.

**Architecture:** Single `SKILL.md` (~250 lines) following Approach A from the spec, runtime router with two `AskUserQuestion` prompts at entry (scope, persona) plus a pre-entry repo-logging check. All three scope branches converge into one shared Socratic engine: opening turn → classify-and-pick-move loop → stuck-offer at 3 stalls → scaffolding ladder during reveal mode. Closes only on explicit user phrase (`stop tutoring`, etc.). Negative-examples list of 10 rules guards against the Socratic posture collapsing. Single source of truth for guardrails matches the Boots-research finding that iteration concentrates in the negative-examples section.

**Tech Stack:** Markdown (SKILL.md), YAML frontmatter, Claude Code skill conventions, `AskUserQuestion` tool, optional `/flagrare:codebase-explore` invocation. Validation via eval-scenario subagent dispatch (the flagrare repo's standard pattern, no unit test framework).

**TDD adaptation:** The artifact is a single Markdown skill, there are no executable test files. The TDD equivalent here is **incremental construction with frequent commits, plus milestone eval validation** at Task 11 (three realistic scenarios run as subagent dispatches, checking Socratic posture, no-answer-leakage, close-phrase exit, and log-append behavior). If an eval reveals a behavior gap, fix it inline and re-eval.

**Spec reference:** `docs/specs/2026-05-28-tutor-skill-design.md`

---

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `plugins/flagrare/skills/tutor/SKILL.md` | Create | The entire skill, frontmatter + all behavior |
| `README.md` | Modify | Add tutor to skill list; update count from 24 → 25 (and "twenty-four" → "twenty-five" in prose) |
| `CHANGELOG.md` | Modify | Add v1.14.0 entry describing the new skill |
| `plugins/flagrare/.claude-plugin/plugin.json` | Modify | Bump version to 1.14.0 |

No new directories needed under `plugins/flagrare/skills/` beyond `tutor/`. No test files (eval pattern is subagent dispatch, not committed test code).

---

## Task 1: Scaffold skill directory and write frontmatter

**Files:**
- Create: `plugins/flagrare/skills/tutor/SKILL.md`

- [ ] **Step 1: Create the skill file with frontmatter and opening prose**

Content for `plugins/flagrare/skills/tutor/SKILL.md`:

````markdown
---
name: tutor
description: "Socratic tutor mode. Switches Claude from doing the work to teaching the user how to do it, via questions instead of answers. User picks scope per call: tutor against current context (file/PR/error), against a named topic, or instead of implementing the thing Claude was about to build. Refuses to give the answer; reveals only when the user explicitly asks or after stuck-detection offers an out. Closes only on explicit close phrase ('stop tutoring', 'end tutor', etc.), no model-side mastery gate. Only triggers on explicit intent: 'tutor me on X', 'tutor me through this', 'tutor mode', 'be my tutor', 'act as a tutor', 'Socratic me', 'use the Socratic method', 'use the tutor skill', '/flagrare:tutor', or 'I don't want the answer, I want to understand'. Does NOT auto-trigger on colloquial phrases like 'teach me', 'explain this', or 'walk me through', those usually mean the user just wants a quick answer."
---

# Tutor

Socratic tutoring mode. Claude switches from doing the work to teaching the user how to do it. **Questions, not answers.** The user produces the understanding; the skill scaffolds the path.

This skill is **explicit-invocation only**. It does not auto-fire on colloquial phrases like "teach me X" or "explain this", those usually mean the user wants a quick answer, not a 20-turn dialogue. Trigger phrases are listed in the frontmatter description above.

---
````

- [ ] **Step 2: Verify the file exists and frontmatter parses**

Run: `head -20 plugins/flagrare/skills/tutor/SKILL.md`
Expected: see the `---` YAML block and `description:` line; no syntax errors visible.

- [ ] **Step 3: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): scaffold skill directory and frontmatter"
```

---

## Task 2: Pre-entry log check section

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append the Step 0 (log check) section**

Append to `plugins/flagrare/skills/tutor/SKILL.md`:

````markdown
## Step 0: Learning-path log check (per-repo, opt-in)

Before entering the mode-selection flow, check whether this repo opts into session logging.

**Project-directory detection.** A directory counts as a project directory if any of these is present at or above the current path: `.git/`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `Gemfile`, `composer.json`, or `mix.exs`. If none of those are found, **skip this entire step**. Do not create `.flagrare/`. Do not ask.

**Marker check.** In a project directory, check `.flagrare/` for:

| Marker present | Behavior |
|---|---|
| `.flagrare/tutor-log.md` | Opt-in confirmed. Will append session summary on close. Skip to Step 1. |
| `.flagrare/tutor-log.disabled` | Opt-out confirmed. Won't log. Skip to Step 1. |
| Neither | First invocation in this repo. Ask the question below. |

**First-invocation question.** Use `AskUserQuestion` with these three options:

- **Yes, log to `.flagrare/tutor-log.md`**: creates the file with a header, appends future sessions
- **No, don't ask again**: creates `.flagrare/tutor-log.disabled` marker
- **Skip for now, ask next time**: neither marker created

If the user chooses **Yes**:
1. Create `.flagrare/tutor-log.md` with this header:
   ```markdown
   # Tutor Learning Path

   Per-session summaries appended by `/flagrare:tutor`. Each H2 entry is one session.
   ```
2. Print: "Created `.flagrare/tutor-log.md`. Add to `.gitignore` if you want it personal, I'm leaving that call to you."
3. Do **not** modify `.gitignore` automatically.

If the user chooses **No, don't ask again**:
1. Create `.flagrare/tutor-log.disabled` as an empty file.
2. Print: "Got it, won't ask again in this repo."

If the user chooses **Skip for now**: do nothing, proceed to Step 1.

---
````

- [ ] **Step 2: Verify the section renders cleanly**

Run: `grep -n "Step 0" plugins/flagrare/skills/tutor/SKILL.md`
Expected: one match.

- [ ] **Step 3: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add per-repo learning-path log opt-in"
```

---

## Task 3: Mode entry: scope and persona questions

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append the Step 1 (scope) section**

Append:

````markdown
## Step 1: Pick the scope

Ask the user via `AskUserQuestion`:

> "What's the scope for this tutoring session?"

Three options:

- **In-context**: tutor against current focus (file/PR/function/error in the conversation)
- **Topic**: tutor against a topic the user names
- **Instead-of-implementing**: tutor instead of building the thing Claude was about to build

Remember the choice for Step 3.

---
````

- [ ] **Step 2: Append the Step 2 (persona) section**

Append:

````markdown
## Step 2: Pick the persona

Ask the user via `AskUserQuestion`:

> "Which tutor persona, ascending intensity?"

Three options:

- **Echo (calm, observational)**: mirrors thinking back, barely a character, steady tone
- **Cipher (puzzle-handler)**: knowing, slightly mysterious, treats every concept as a puzzle to crack
- **Vex (pushes hard)**: leading, slightly antagonistic-but-caring, treats frustration as part of the curriculum

Persona affects **voice only**: not branch logic, not guardrails, not the Socratic engine. Adopt the chosen voice consistently for the rest of the session.

**Echo voice example:** "OK. So `session.userId` is checked. What if `session` itself is undefined here?"

**Cipher voice example:** "Right, the check is there. Here's the puzzle: what makes you confident `session` exists at all?"

**Vex voice example:** "Sure, you checked `userId`. Now think harder: where does `session` come from, and why are you assuming it's there?"

---
````

- [ ] **Step 3: Verify both sections present**

Run: `grep -nE "^## Step [12]" plugins/flagrare/skills/tutor/SKILL.md`
Expected: two matches, one per step.

- [ ] **Step 4: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add scope and persona selection at entry"
```

---

## Task 4: Three scope branches

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append the Step 3 dispatcher + Branch 1 (in-context)**

Append:

````markdown
## Step 3: Enter the chosen scope branch

Dispatch on the Step 1 choice. Each branch confirms scope, loads context, then hands off to the Socratic engine in Step 4.

### Branch 1: In-context

Identify what's currently in focus from the conversation: most recently read file, current PR if referenced, last named function, last error or stack trace. Pick the single most-likely candidate.

Confirm with the user via **free text** (not `AskUserQuestion`, open-ended rename is more useful here):

> "Tutoring you against `[identified scope]`, the [file/function/PR/error] we were just looking at. Confirm scope, or name something different."

On confirmation (or rename) → Step 4.

If nothing is in focus (fresh session, no prior reads), ask the user directly: "I don't see anything in context to tutor against. Name a file, function, or error to focus on."

---
````

- [ ] **Step 2: Append Branch 2 (topic)**

Append:

````markdown
### Branch 2: Topic

Ask the user to name the topic via free text. Enforce specificity:

> "What topic? Be specific, 'React Suspense' or 'how async iterators work in Python' is good. 'JavaScript' or 'databases' is too broad and the session will go in circles."

If the user names a too-broad topic, push back once: "Too broad. Narrow down, pick a sub-topic or one concrete question." Do not start the dialogue against a too-broad topic.

**Optional codebase grounding.** If the topic intersects with the local codebase ("teach me how auth works *here*", "Socratic me on the way we handle migrations in this repo"), invoke `/flagrare:codebase-explore` first to gather concrete file paths and patterns. Use those findings to ground the opening question. If the topic is purely conceptual ("teach me how async iterators work"), skip codebase-explore and proceed.

Hand off to Step 4.

---
````

- [ ] **Step 3: Append Branch 3 (instead-of-implementing)**

Append:

````markdown
### Branch 3: Instead-of-implementing

Scan the **current conversation** for what Claude was about to implement. Look for: an active plan (recent `EnterPlanMode` / `ExitPlanMode` artifact), a recent `TaskCreate` list, an "I'll build X" / "let me implement X" statement, or a pending refactor.

**If one or more candidates are detected**, present them via `AskUserQuestion` with each candidate as an option. `AskUserQuestion` always includes an implicit "Other", the user can type a custom task there.

> "What should I be teaching you to build?"
>
> - Implement `[detected candidate 1]` (auto-detected from this conversation)
> - Implement `[detected candidate 2]` (if found)
> - Other (you'll type it)

**If nothing was auto-detected**, ask via free text: "I don't see anything I was about to implement. What should I be teaching you to build?"

**Stated promise on entry (load-bearing).** Before the first Socratic question, say this verbatim (adapted to the persona's voice):

> "I was about to implement `[task]`. Switching to teaching you how to build it instead. **My intended solution stays in my context. I won't show it.** You'll write the code. I'll ask questions until you do."

This is the prompt-level commitment that holds the Branch 3 guardrail. Breaking it is the worst failure mode in the entire skill (rule #10 in the negative-examples list).

Hand off to Step 4.

---
````

- [ ] **Step 4: Verify all three branches present**

Run: `grep -nE "^### Branch [123]" plugins/flagrare/skills/tutor/SKILL.md`
Expected: three matches.

- [ ] **Step 5: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add three scope branches (in-context, topic, instead-of-implementing)"
```

---

## Task 5: Socratic engine: opening turn and turn loop

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append Step 4 opening turn**

Append:

````markdown
## Step 4: Socratic engine

All three branches converge here. The engine runs until the user invokes a close phrase (see Step 7).

### Opening turn

Always open with a posture statement followed by a calibration question. Use the persona's voice but keep this structure:

> "OK, tutoring you against `[scope]`. I'm going to ask, not tell. Say **'stop tutoring'** whenever you want to exit. If you want me to just show you instead, say so. Let's start: **[opening question]**"

The opening question probes the user's existing mental model rather than starting from scratch. Pick by branch:

| Branch | Opening question shape |
|---|---|
| In-context | "Walk me through what you think this code is doing." |
| Topic | "What's your current understanding of `[topic]`?" |
| Instead-of-implementing | "How would you start? Don't write code yet, talk me through your approach." |

The "say so if you want me to just show you" line is the **always-visible escape hatch**. Do not omit it.

---
````

- [ ] **Step 2: Append the turn loop**

Append:

````markdown
### Turn loop

Every dialogue turn after the opening follows this loop.

**Classify the user's last response** into one of:

- `converging`, on the right track, partially or fully correct
- `partial`, got part of it, missing a piece
- `wrong-or-confused`, wrong direction, or visibly confused
- `stalled`, wrong again on a near-repeat, "I don't know," empty/short reply, or expressed frustration
- `reveal-requested`, user explicitly asked for the answer ("just tell me", "give up", "show me", "I want the answer")

**Pick the move** for that state:

| State | Move | Shape |
|---|---|---|
| `converging` | Affirm + sharpen | Name what they got right with one specific phrase, then push one level deeper. Example: "Right, `session.userId` is checked. Now: what if `session` itself is undefined?" |
| `partial` | Redirect via question | Counterexample question that exposes the gap. Example: "OK. What would your version return if `userId` were `0`?" |
| `wrong-or-confused` | Scaffold down a rung | More basic preceding question. Example: "Step back, what's the type of `req.session` at that point?" |
| `stalled` | Increment stall counter. If 3 consecutive stalls, trigger the **stuck-offer** (Step 5). Otherwise, scaffold down. | (See Step 5 for stuck-offer.) |
| `reveal-requested` | Enter reveal mode at the user's chosen rung (Step 6). | (See Step 6 for ladder.) |

**Output exactly one question per turn.** Hard rule. No multi-question turns. No lectures. No code blocks during dialogue. Inline code references like `req.session` are fine; full snippets are not until reveal mode.

Reset the stall counter to zero on any non-stall response.

---
````

- [ ] **Step 3: Verify Step 4 sections present**

Run: `grep -nE "^### (Opening turn|Turn loop)" plugins/flagrare/skills/tutor/SKILL.md`
Expected: two matches.

- [ ] **Step 4: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add Socratic engine opening turn and turn loop"
```

---

## Task 6: Stuck-offer and scaffolding ladder

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append Step 5 stuck-offer**

Append:

````markdown
## Step 5: Stuck-offer (escape hatch at 3 stalls)

When the stall counter hits **3 consecutive stalls**, break the dialogue briefly and offer the escape via `AskUserQuestion`:

> "You've stalled three times. I can give you a sharper hint, or just show you, your call. Or keep going if you want another shot."

Three options:

- **Keep going**: reset the stall counter to zero and continue dialogue. The user has chosen to push through.
- **Sharper hint**: enter reveal mode at **rung 1** (Step 6).
- **Show me**: enter reveal mode at **rung 3** (Step 6).

The stuck-offer is the only place the engine breaks the "one question per turn" rule (the offer itself is structured as a 3-option `AskUserQuestion`, not a dialogue question). After the user's choice, return to the engine state defined by that choice.

---
````

- [ ] **Step 2: Append Step 6 scaffolding ladder**

Append:

````markdown
## Step 6: Scaffolding ladder (reveal mode only)

Reveal mode is entered only via (a) the user explicitly asking for the answer, or (b) the user accepting the stuck-offer's "sharper hint" or "show me" path. **Never enter reveal mode autonomously.**

Three rungs, ascending specificity:

| Rung | What's revealed | Example |
|---|---|---|
| 1, Sharper hint | A concrete pointer to the right region. Still a question. | "Look at where `session` is initialized. What's the default value before the request handler runs?" |
| 2, Near-reveal | The mechanism stated, the application still asked. | "`session` is `undefined` when the cookie's missing. So what does your check need to handle that case?" |
| 3, Full reveal | The answer + *why* it's the answer + one local verify-back question. | "It's `req.session?.userId ?? null`. The `?.` handles the undefined session, the `??` keeps the explicit-null contract. **Quick check before we move on**: what would `?.` do differently than `&&` here?" |

The local verify-back question at rung 3 is **not the session close**: it's a local check before continuing the dialogue. The user can still answer it incorrectly without ending the session. The session close is explicit-phrase only (Step 7).

If the user requested reveal without specifying a rung, default to **rung 1** and only escalate if they ask again.

After rung 3, the topic of that specific question is closed. Pick up the next thread or wait for the user's next direction.

---
````

- [ ] **Step 3: Verify both steps present**

Run: `grep -nE "^## Step [56]" plugins/flagrare/skills/tutor/SKILL.md`
Expected: two matches.

- [ ] **Step 4: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add stuck-offer and 3-rung scaffolding ladder"
```

---

## Task 7: Negative examples (10 seed rules)

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append the negative-examples section**

Append:

````markdown
## Negative examples: what the tutor must never do

Seed list of 10 rules. Per the Boots research, this is where iteration will concentrate, every observed failure should become a new rule here.

1. **Never reveal the answer** unless the user explicitly asked or accepted a stuck-offer's "sharper hint" or "show me" path.
2. **Never ask multiple questions in one turn.** One question, one focus.
3. **Never lecture.** Every dialogue-mode turn ends with a question.
4. **Never dump code blocks during dialogue mode.** Inline references like `req.session` are fine; full snippets aren't until reveal mode (rung 2 or 3).
5. **Never use empty validators** like "Great question!" / "Good thinking!", give one specific phrase or none.
6. **Never apologize for asking.** "Sorry to keep asking" is the strongest signal of a tutor about to fold and tell.
7. **Never falsely validate.** If the user got it wrong, the next move is a redirect question, not "yes, sort of, but…".
8. **Never repeat the same question after a stall.** Rephrase or scaffold down a rung.
9. **Never drift off-topic.** If the user asks something unrelated mid-session, redirect: "Park that, back to X."
10. **In Branch 3: never let the canonical solution into the turn.** It stays in Claude's context. The user has to produce their own version. The skill made a stated promise, breaking it is the worst failure mode.

---
````

- [ ] **Step 2: Verify the section is present**

Run: `grep -nE "^## Negative examples" plugins/flagrare/skills/tutor/SKILL.md`
Expected: one match.

- [ ] **Step 3: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add 10 negative-example guardrails"
```

---

## Task 8: Close and log append

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append Step 7 close**

Append:

````markdown
## Step 7: Close

**Explicit user action only.** No verify-back gate at session end.

Listen for any of these close phrases from the user:

- `stop tutoring`
- `stop tutor`
- `end tutor`
- `exit tutor mode`
- `we're done tutoring`
- `close tutor`

On any of those, exit the engine cleanly. No comprehension check, no recap **unless the user explicitly asks for one** (e.g., "give me a quick recap before we wrap", in which case respond with a single paragraph summary, then close).

The trade-off is intentional: users can exit thinking they understand when they don't. That risk is on the user, not on a flaky model-side gate.

### Log append (only if `.flagrare/tutor-log.md` exists)

If, and only if, `.flagrare/tutor-log.md` exists at the project root (the user opted into logging in Step 0), append a structured H2 entry before exiting:

```markdown
## [YYYY-MM-DD]: Branch [N] ([branch name]), [Persona]
**Topic**: [scope name]
**Covered**: [1-3 short phrases naming the concepts the dialogue actually traversed]
**Stuck on**: [1 short phrase, or "none" if no stalls were hit; note how many stuck-offers were accepted and at what rung]
**Reveal level reached**: [rung number reached, or "none" if no reveal was triggered]
```

Real example:

```markdown
## 2026-05-28: Branch 3 (instead-of-implementing), Vex
**Topic**: `handleSessionTimeout()` design
**Covered**: optional chaining behavior with undefined sessions; the `?? null` vs `&& null` distinction
**Stuck on**: when session.userId is `0` vs `undefined` (1 stuck-offer accepted at rung 2)
**Reveal level reached**: rung 2 (near-reveal accepted, rung 3 not needed)
```

Append to the file with a blank line separator before the new H2. Do not modify the file's existing entries or header.

After appending, print: "Session logged to `.flagrare/tutor-log.md`."

If the log file does **not** exist (user chose "No" or "Skip" in Step 0), exit silently without printing.

---
````

- [ ] **Step 2: Verify Step 7 present**

Run: `grep -nE "^## Step 7" plugins/flagrare/skills/tutor/SKILL.md`
Expected: one match.

- [ ] **Step 3: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add explicit close and learning-path log append"
```

---

## Task 9: Cross-skill integration and re-entry rules

**Files:**
- Modify: `plugins/flagrare/skills/tutor/SKILL.md` (append)

- [ ] **Step 1: Append the final sections**

Append:

````markdown
## Cross-skill integration

Deliberately minimal. Three integration points only:

1. **Branch 2 → `/flagrare:codebase-explore`** (optional), invoke when the topic intersects local code. Use the findings to ground the opening question. Skip for purely conceptual topics.
2. **Branch 3 starting context**: pure read of the current conversation for implementation candidates. No skill call.
3. **At close: no automatic handoff.** Do not suggest `/flagrare:smoke-test`, `/flagrare:implementation-review`, or any other skill. The user decides what to do next.

## Re-entry and interruption

- **Stateless across invocations.** Re-invoking `/flagrare:tutor` mid-session is a **fresh start**. No resume of prior dialogue, no carry-over of stall counters or persona choice.
- **Tutor takes over inside other skills.** If the user is inside `/flagrare:atdd-plan`, `/flagrare:intake`, or any other flagrare skill and invokes `/flagrare:tutor`, this skill takes over. No graceful resume of the prior skill. The user can re-invoke the prior skill manually after the tutor session closes.
- The `.flagrare/tutor-log.md` file is the only cross-session persistence in the design.
````

- [ ] **Step 2: Verify the file looks complete**

Run: `wc -l plugins/flagrare/skills/tutor/SKILL.md && grep -c "^##" plugins/flagrare/skills/tutor/SKILL.md`
Expected: between 200 and 320 lines; ~10 H2 sections (Step 0 through Step 7, Negative examples, Cross-skill integration, Re-entry).

- [ ] **Step 3: Commit**

```bash
git add plugins/flagrare/skills/tutor/SKILL.md
git commit -m "✨ feat(tutor): add cross-skill integration and re-entry rules"
```

---

## Task 10: Update README and version files

**Files:**
- Modify: `README.md`
- Modify: `plugins/flagrare/.claude-plugin/plugin.json`

- [ ] **Step 1: Update README skill count and add tutor entry**

In `README.md`:

1. Update the opening sentence count (currently "Twenty-four skills"): change to "Twenty-five skills".
2. Update the numeric count in the next sentence (currently "twenty-four skills"): change to "twenty-five skills".
3. Add a "Learning" subsection (or extend the most thematically adjacent existing subsection) describing `/flagrare:tutor`. Recommended placement: after the Planning section. The entry should follow the existing one-paragraph-per-skill style, describe what it does, the three modes, the persona slots, and that it logs to `.flagrare/tutor-log.md` if opted in.

Suggested entry text:

> `/flagrare:tutor` switches Claude from doing the work to teaching the user how to do it via the Socratic method, questions, not answers. User picks scope per call: tutor against current context (file/PR/error), against a named topic, or instead of implementing the thing Claude was about to build. Three persona slots in ascending intensity, Echo (calm), Cipher (puzzle-handler), Vex (pushes hard). Refuses to give the answer; reveals only when the user asks or after stuck-detection at three stalls offers an out. Closes on explicit phrase only ("stop tutoring"). On first invocation in a repo, asks whether to record per-session summaries to `.flagrare/tutor-log.md` as a learning-path log.

- [ ] **Step 2: Bump plugin version**

In `plugins/flagrare/.claude-plugin/plugin.json`:

Read the current version string. Bump the **minor** segment (e.g., `1.13.5` → `1.14.0`) since this is a new feature, not a fix or release-only change. Reset the patch to 0.

- [ ] **Step 3: Verify README and plugin.json updates**

Run: `grep -c "tutor" README.md && grep version plugins/flagrare/.claude-plugin/plugin.json`
Expected: at least 1 match for "tutor" in README; plugin.json shows the bumped version.

- [ ] **Step 4: Commit**

```bash
git add README.md plugins/flagrare/.claude-plugin/plugin.json
git commit -m "✨ feat(tutor): document tutor skill in README and bump version to 1.14.0"
```

---

## Task 11: Add CHANGELOG entry

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add v1.14.0 entry at the top of CHANGELOG.md (just below the `# Changelog` header)**

Use the existing changelog format (one-line headline summary, then `### Behaviour` bullets). The entry follows this shape (adapt phrasing to match the established voice, value-focused, user-facing, no implementation chatter):

```markdown
## 1.14.0: 2026-05-28

`/flagrare:tutor` is a new Socratic tutoring mode that switches Claude from doing the work to teaching the user how to do it, via questions instead of answers. User picks scope and persona per call. Closes only on explicit phrase. Optional per-repo learning-path log.

### Behaviour

- **`/flagrare:tutor`, three scope modes**: in-context (against current file/PR/function/error), topic (user names what to learn), or instead-of-implementing (Claude was about to build something; user opts to learn how to build it instead and writes the code themselves).
- **`/flagrare:tutor`, three personas, ascending intensity**: Echo (calm, observational), Cipher (knowing, puzzle-handler), Vex (pushy, leading). Persona affects voice only, same Socratic engine underneath.
- **`/flagrare:tutor`, Socratic guardrails**: refuses to reveal the answer unless the user explicitly asks. Stuck-detection at three consecutive stalls offers a sharper-hint, show-me, or keep-going escape. Reveal mode has a 3-rung scaffolding ladder ending in a local verify-back question.
- **`/flagrare:tutor`, explicit-phrase close only**: exits on "stop tutoring", "end tutor", "exit tutor mode", or similar. No model-side mastery gate.
- **`/flagrare:tutor`, per-repo learning-path log (opt-in)**: on first invocation in a project directory, asks whether to record per-session summaries to `.flagrare/tutor-log.md`. Opt-out is per-repo and silent on subsequent calls. Non-project directories skip logging entirely.
- **`/flagrare:tutor`, explicit-trigger only**: fires only on phrases like "tutor me on X", "tutor mode", "be my tutor", "Socratic me", or "/flagrare:tutor". Does NOT auto-trigger on colloquial "teach me X" or "explain this", those usually mean the user wants a quick answer.
```

- [ ] **Step 2: Verify the entry is at the top of CHANGELOG.md**

Run: `head -25 CHANGELOG.md`
Expected: `## 1.14.0 — 2026-05-28` appears before any prior version entries.

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "📝 docs(tutor): add v1.14.0 CHANGELOG entry"
```

---

## Task 12: Eval validation: three realistic scenarios

**Files:** none modified by this task (eval-only, no code changes)

This task substitutes for the unit-test pass that a code feature would normally end with. Dispatch three subagents, each running one realistic scenario against the just-built skill. Check the outputs against acceptance criteria. If any criterion fails, return to the relevant task above, fix the SKILL.md inline, and re-run the failing eval.

- [ ] **Step 1: Dispatch eval 1, in-context Socratic posture**

Spawn a subagent (`general-purpose`) with this prompt:

> Simulate a developer using `/flagrare:tutor`. You are working on `src/auth/middleware.ts` and just read the file. You ask the model to tutor you against the `handleSession()` function. Pick scope=in-context, persona=Echo. Then, in dialogue, give a deliberately wrong answer to the opening question ("it checks if the user is logged in"), but don't ask for the answer. Verify that the tutor (a) refuses to reveal the answer, (b) asks exactly one question per turn, (c) scaffolds down a rung when you got it wrong, (d) does not lecture. After 5 dialogue turns, say "stop tutoring" and verify the session exits cleanly without a verify-back gate. Report each criterion as PASS or FAIL with one sentence of evidence.

Expected: 4 PASS results.

- [ ] **Step 2: Dispatch eval 2, instead-of-implementing stated-promise hold**

Spawn a subagent with this prompt:

> Simulate a developer using `/flagrare:tutor`. Set context: Claude was about to implement a function `userSessionTimeout()` (you can describe the intended behavior, auto-extend on activity vs. hard timeout). Invoke the tutor with scope=instead-of-implementing, persona=Vex. After the stated promise ("I won't show it"), give a vague answer ("uh, like, check if time passed?"). Stall 3 times. Accept the stuck-offer's "show me" path. Verify that (a) the tutor states the no-reveal promise verbatim before the first question, (b) the tutor never inserts a full code block during the 3 stall turns, (c) the stuck-offer fires on the 3rd stall, not earlier or later, (d) when "show me" is chosen, the reveal is at rung 3 with the answer + why + one local verify-back question, (e) the reveal does NOT auto-close the session, the user still has to say "stop tutoring". Report PASS/FAIL per criterion.

Expected: 5 PASS results.

- [ ] **Step 3: Dispatch eval 3, log opt-in and append on close**

Spawn a subagent with this prompt:

> Simulate a developer using `/flagrare:tutor` in a fresh repo with a `.git/` directory but no `.flagrare/`. Verify that (a) the first-invocation question fires, (b) accepting "Yes, log to `.flagrare/tutor-log.md`" creates the file with the documented header, (c) the skill prints the `.gitignore` suggestion without modifying `.gitignore`, (d) after a short dialogue and "stop tutoring", a new H2 entry is appended to `tutor-log.md` matching the documented format (date, branch, persona, topic, covered, stuck on, reveal level), (e) re-invoking the skill does NOT re-ask the log question because the marker file exists. Report PASS/FAIL per criterion. Use a scratch directory like `/tmp/tutor-eval-3/` to avoid polluting real repos.

Expected: 5 PASS results.

- [ ] **Step 4: Triage results**

If all three evals report all PASS, proceed to Step 5. If any criterion is FAIL:

1. Identify which SKILL.md section governs the failed behavior.
2. Re-open the relevant Task above (e.g., Task 7 for negative-example rule failures, Task 6 for stuck-offer issues).
3. Tighten the offending instruction.
4. Commit the fix with a `🔧 fix(tutor): <specific behavior fixed>` message.
5. Re-run the failed eval only.
6. Repeat until all PASS.

- [ ] **Step 5: Document eval results in this plan file**

Append a brief results block to **this plan file** (so the record persists with the plan):

```markdown
## Eval Results

- **Eval 1 (in-context Socratic posture)**: [PASS/FAIL summary]
- **Eval 2 (instead-of-implementing promise hold)**: [PASS/FAIL summary]
- **Eval 3 (log opt-in and append)**: [PASS/FAIL summary]

Fixes applied during validation: [list any commits made during Step 4, or "none" if all evals passed first run.]
```

- [ ] **Step 6: Commit eval results**

```bash
git add docs/plans/2026-05-28-tutor-skill.md
git commit -m "✅ test(tutor): record eval validation results"
```

---

## Self-Review checklist (run before declaring the plan complete)

This is the writer's checklist, run it against the just-finished plan and fix anything that's off before handing off.

**Spec coverage**: every spec section maps to a task:

| Spec section | Implemented in |
|---|---|
| Skill identity (name, file, architecture) | Task 1 |
| Trigger surface (explicit-intent only + DOES-NOT-TRIGGER negatives) | Task 1 (frontmatter) |
| Pre-entry log check (markers, project detection, opt-in) | Task 2 |
| Q1 scope | Task 3 |
| Q2 persona | Task 3 |
| Branch 1 in-context | Task 4 |
| Branch 2 topic + codebase-explore | Task 4 |
| Branch 3 instead-of-implementing + stated promise | Task 4 |
| Opening turn | Task 5 |
| Turn loop (classify → move) | Task 5 |
| Stuck-offer (3 stalls) | Task 6 |
| Scaffolding ladder (3 rungs) | Task 6 |
| 10 negative-examples | Task 7 |
| Explicit close phrase | Task 8 |
| Log append on close | Task 8 |
| Cross-skill integration (minimal) | Task 9 |
| Re-entry / interruption | Task 9 |
| README + version bump | Task 10 |
| CHANGELOG entry | Task 11 |
| Validation (substitutes for unit tests) | Task 12 |

No spec sections uncovered.

**Placeholder scan**: no "TBD", "TODO", "fill in", "similar to Task N without repetition", or "implement appropriate X" anywhere in the plan. Verified.

**Type consistency**: names used across tasks: `Echo` / `Cipher` / `Vex` (persona slots), `Branch 1` / `Branch 2` / `Branch 3` (scope branches), `Step 0` through `Step 7` (skill flow), `rung 1` / `rung 2` / `rung 3` (scaffolding), `.flagrare/tutor-log.md` and `.flagrare/tutor-log.disabled` (marker files). All consistent across tasks.

---

## Eval Results

Ran 2026-05-28 against the completed SKILL.md at commit `6f5315e`. Three subagent-dispatched scenarios, sonnet model, simulated user + Claude-executing-skill role-play with PASS/FAIL verification against acceptance criteria.

- **Eval 1 (in-context Socratic posture)**: **6/6 PASS**. Posture statement with `'stop tutoring'` mention and always-visible escape hatch present; exactly one question per turn across 5 dialogue turns; scaffold-down move on wrong answer (turn 2 went to a more basic preceding question rather than repeating or correcting); zero empty validators ("Great question!" etc.); clean exit on "stop tutoring" without verify-back gate; no answer leakage at any turn.
- **Eval 2 (instead-of-implementing promise hold)**: **7/7 PASS**. Stated promise fired verbatim including the bolded "My intended solution stays in my context. I won't show it." line in Vex's voice; no full code blocks across the 3 stalled turns; stuck-offer triggered on the 3rd stall exactly (not 2nd, not 4th); rung-3 reveal contained answer + why + one local verify-back question; vague post-reveal answer ("yeah that makes sense") did NOT auto-close the session, Claude continued the dialogue per Step 6's "local verify-back is not the session close" rule; Vex's pushy-but-caring voice held consistently; close only triggered on explicit "stop tutoring".
- **Eval 3 (log opt-in and append)**: **7/7 PASS**. First-invocation question fired in fresh project directory; `.flagrare/tutor-log.md` created with exact header on Yes; `.gitignore` was NOT auto-modified (skill leaves the call to the user); H2 entry appended on close with correct structured-field format; existing header preserved character-for-character; blank-line separator between header and new entry; re-invocation marker check would find the file and skip the question (filesystem state verified).

**Fixes applied during validation**: none. All 20 acceptance criteria across the three scenarios passed on first run.
