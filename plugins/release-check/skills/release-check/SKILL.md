---
name: release-check
description: Post-commit gate. Invoke after every commit (right after /staleness-audit). Checks whether a release is due, and if so, proposes a semver bump and a value-focused CHANGELOG entry modeled on Valve's Dota 2 patch notes — describing what the user gains, never what was refactored. Acts on approval.
---

# Release check

## When to invoke

After every commit, immediately after `/staleness-audit`. Cheap to run when there's nothing to do (early-exit ~1 second). The user's binding rule (saved in agent memory) says: every commit triggers this check.

You should also invoke this on demand whenever the user asks "is a release due?", "let's ship this", "what would v0.2 look like?", or similar.

## Procedure

### 1. Read inputs (cheap)

- `package.json` → current `version`, `private` flag, `name`
- `.changeset/*.md` (excluding `README.md` and `config.json`) → pending changes
- `CHANGELOG.md` if present → previous release entries (for stylistic continuity)

### 2. Compute pending bump

For each `.changeset/*.md`, read the frontmatter. It looks like:

```
---
"poltergink": minor
---
```

Aggregate by level:
- Any `"major"` → proposed bump is **major**
- Else any `"minor"` → proposed bump is **minor**
- Else any `"patch"` → proposed bump is **patch**
- Else → no pending changesets, **release is not due**

Compute the proposed version from the current one by applying the bump (semver rules: 0.x.y treats `minor` like `major` would in 1.x.y — breaking changes are allowed in 0.x without major bumps).

### 3. Decide: is the release DUE?

| State | Decision |
|---|---|
| No pending changesets | **Not due** — done, early exit |
| Pending + `private: true` and proposed version still in 0.0.x range | **Not due yet** — pre-feature release; surface the proposal as a heads-up |
| Pending + `private: true` and proposed version is 0.1.0+ | **Due if the headline feature is in** — present the proposal, ask the user |
| Pending + `private: false` and any `major` | **Due now** |
| Pending + `private: false` and ≥ 1 `minor` or ≥ 3 `patch` | **Due** — propose to ship |
| Pending + `private: false` and < 3 `patch` only | **Soft due** — propose but flag it could wait |

These are heuristics. Trust your judgment: a single security-fix `patch` ships immediately; ten cosmetic `patch`es probably batch.

### 4. If DUE, draft the value-focused CHANGELOG entry

**This is the part that takes care.** The default `pnpm changeset version` output inherits the changeset summary text directly — that text is often written tersely by the author and leans technical. Rewrite it before commit.

The model is **Valve's Dota 2 patch notes** as actually published (see e.g. <https://liquipedia.net/dota2/Version_7.36>, not your memory of them). The reader is the consumer of the library, not its author. They want: "what can I do now that I couldn't before, and how does my code need to change?"

#### Style (calibrated to actual Valve patches)

**Section headers — Title Case.** Not ALL CAPS. Examples Valve uses: "General Mechanics", "Map Changes", "Hero Adjustments", "Item Changes", "Bug Fixes". For a TS library, the spiritual equivalents:

- `## General` — top-level capabilities and breaking changes
- `## Public API` — new exports, signature changes, deprecations
- `## Behaviour` — things that work differently now without an API change
- `## Performance` — measurable wins the user will notice
- `## Bug Fixes` — terminal section, purely factual, no detail beyond "what was broken, fixed"

Skip a section entirely if it has nothing in it. Better to have fewer sections that each carry weight.

**Per-entry shape — bold anchor + colon + delta.** Valve's canonical pattern:

```
- **Bloodstone**: spell lifesteal 30% → 20%.
- **Templar Assassin**: Refraction shields 30/40/50/60 → 20/30/40/50.
- **Anti-Mage**: major rework — new innate 'Persecutor' applies
  movement-speed slow based on enemy mana.
```

For a TS library, the anchor is the symbol the user calls:

```
- **`Session.run()`**: now returns a frozen `Transcript` instead of
  a plain object. Shape is a superset — `turns` and `finalScene`
  are where they were.
- **`StoryChoiceRangeError`**: carries `.attempted` and `.available`
  for typed handling without parsing `.message`.
```

**Length per entry — one line for simple deltas, 2–3 lines for reworks chained with semicolons.** Match Valve's density.

**Use the `→` arrow for numerical or behavioural deltas.** `"Cooldown 7s → 18s"`, `"Coverage threshold 80% → 75%"`. Two characters, instantly readable.

**Tense — declarative, present, sentence fragments.** Mix matches Valve's: "Refraction shields …" not "We changed Refraction shields …", "Sessions now expose …" not "Added event emission …".

**What goes in:**
- Concrete user-callable changes (new exports, behaviour shifts, error-shape changes).
- Numerical deltas with `→`.
- Breaking changes with a one-line migration hint when non-obvious.
- Bug fixes the user might have hit, as a terminal `## Bug Fixes` section, purely factual.

**What stays out:**
- Refactors that don't change behaviour (type-alias renames where the shape is compatible, file moves, internal-module re-orgs).
- Build/lockfile/lint config changes.
- Test framework migrations.
- ADR creation (cross-reference if a breaking change is rooted in an ADR, but don't make the ADR the entry).
- PR numbers, SHAs, branch names.
- The *why* — unless it's a security fix or a breaking-change rationale the user needs.

#### Good vs bad — concrete examples

✅ Valve-calibrated (what the user reads):

```markdown
## 0.1.0 — 2026-05-18

The first release that drives an Ink narrative end-to-end. Pick a
Player, hand it a Story, get a frozen Transcript and live events.

### Public API

- **`Story.fromInk(source)` / `Story.fromJson(json)`**: load an Ink
  narrative from raw source or pre-compiled JSON. Compiler is
  bundled — no inklecate needed.
- **`Story.advance()`**: drives the story to the next branch point;
  returns the accumulated text, passage tags, and the choices to
  pick from.
- **`Story.choose(index)`**: out-of-range or non-integer indices
  reject with `StoryChoiceRangeError` carrying `.attempted` and
  `.available`.
- **`Story.snapshot()` / `Story.restore(json)`**: round-trippable
  state JSON for save/load.
- **`Session({ story, player })`**: runs the turn loop; returns a
  frozen `Transcript`.
- **`ScriptedPlayer([0, 1, 0])`**: deterministic Player for tests
  and replays. `ScriptExhaustedError` carries `.scriptLength` and
  `.turnIndex`.
- **`Transcript`**: every `TurnRecord` includes `snapshotBefore` /
  `snapshotAfter`. Replay from any turn via `story.restore(turn.
  snapshotBefore)`.
- **`Session.on(type, listener)`**: typed events `turn:start`,
  `choice:made`, `story:ended`. Returns an unsubscribe.
- **`maxTurns`** option on `Session`: throws
  `SessionMaxTurnsError` with the partial Transcript on overrun.

### Behaviour

- Per-choice tags written **before** the bracketed choice text
  populate `Choice.tags`; tags **after** the brackets surface on
  the next `Scene.tags`. This is the hook the upcoming
  `PersonaDirector` reads.

### Known Limits

- No `LLMPlayer` yet — bring your own `Player`, or drive with
  `ScriptedPlayer` until v0.2.
```

❌ Engineering changelog (the thing to NOT write — and what `pnpm changeset version` will produce verbatim if not rewritten):

```
## 0.1.0

- Refactored `SessionResult` → `Transcript` (breaking type rename)
- Added EventEmitter pattern to Session via `Map<EventType, Set<Listener>>`
- Added `Object.freeze` to TurnRecord and Transcript construction
- Pinned `@typescript-eslint/parser` to `8.59.3`
- Migrated tests from Cucumber to Vitest (see ADR-0003)
- Bumped `typescript` peer range
```

### 5. Present the proposal

Use this exact shape so the user can scan it fast:

```
Release check: DUE / NOT DUE / SOFT-DUE
Current version: x.y.z   →   Proposed: x.y.z

Pending changesets (N):
  - <slug>.md   <level>   <one-line summary>

Proposed CHANGELOG entry:

  ## x.y.z — YYYY-MM-DD

  **NEW CAPABILITIES**
  - …
  - …

  **BEHAVIOUR CHANGES**
  - …

  **BREAKING CHANGES**
  - …

Action plan:
  1. Run `pnpm changeset version` (bumps package.json, consumes
     changesets, generates draft CHANGELOG).
  2. Overwrite the generated CHANGELOG entry with the rewrite above.
  3. Commit `🔖 release: vX.Y.Z`.
  4. Tag `vX.Y.Z` and push (`--tags`).
  5. If `private: false` and the workflow exists, trigger the
     Release action from the Actions tab (or have it run on push
     if auto-trigger is on). Otherwise stop at step 4.

Approve to proceed?
```

If NOT DUE:

```
Release check: not due. <one-line reason>.
Pending: N changesets, would propose vX.Y.Z when ready.
```

### 6. On approval, execute the plan

Run the steps in order. After each, verify the previous step succeeded. If `pnpm changeset version` fails or produces unexpected output, stop and surface — do not silently push.

For the CHANGELOG rewrite specifically:

1. Capture the auto-generated CHANGELOG entry as a reference (do **not** ship it).
2. Replace that block with the value-focused rewrite.
3. Run `pnpm verify` to make sure the version bump didn't break anything that depends on package.json (it usually won't).
4. Stage and commit with `🔖 release: vX.Y.Z` (matches commitlint).
5. Tag: `git tag vX.Y.Z`.
6. Push: `git push origin main --follow-tags`.

## Anti-patterns

- **Don't release just because changesets exist.** A single typo-fix changeset for a private package isn't a release event.
- **Don't write the changelog from the diff.** Write from intent — read the changeset summary, the commit body, then translate to what the user *gains*. The diff is misleadingly engineering-shaped.
- **Don't ship the auto-generated CHANGELOG without rewriting.** Changesets' default output is fine as a starting point; it is not fine to publish.
- **Don't bypass the user's approval for the actual release.** Propose, wait, then act. Releases are public, hard to reverse.
- **Don't add a section that's empty.** Skip `**FIXES**` if there are no fixes; better to have fewer sections that each carry weight.

## Cross-references

- `/staleness-audit` runs *before* this check, on the commit being created. This check runs *after* the commit lands, since release decisions depend on `package.json` + `.changeset/` state as they exist post-commit.
- `feedback-post-commit-release-check` in agent memory mandates invoking this skill.
- Valve's Dota 2 patch notes: <https://www.dota2.com/news/updates> — the canonical reference for the changelog style this skill enforces.

## Why this exists

A library's CHANGELOG is the first thing a prospective user reads after the README. Tooling like Changesets makes it easy to *generate* one and easy to write a bad one — the default flow stitches together author-written summaries verbatim, which often read like a Git log. Valve's Dota patch notes are the canonical example of how to write a changelog the audience actually wants: every line is a thing the player can observe, not a thing the engineers did. Same principle for libraries: the user wants to know what they can do now, what they need to update, and what bugs they no longer have. Nothing else.
