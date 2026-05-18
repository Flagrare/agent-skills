---
name: release-check
description: Post-commit gate. Invoke after every commit (right after /staleness-audit). Checks whether a release is due, and if so, proposes a semver bump and a value-focused CHANGELOG entry modeled on Valve's Dota 2 patch notes — describing what the user gains, never what was refactored. Acts on approval.
---

# Release check

## When to invoke

After every commit, immediately after `/staleness-audit`. Cheap to run when there's nothing to do (early-exit ~1 second).

Also invoke on demand whenever the user asks "is a release due?", "let's ship this", "what would v0.2 look like?", or similar.

## Procedure

### 1. Detect the project's release mechanism

Before reading inputs, identify how this project tracks and ships releases:

| Signal | Mechanism |
|---|---|
| `.changeset/` directory present | **Changesets** (`pnpm/npm/yarn changeset`) |
| `changelog.d/` directory present | **towncrier** |
| `CHANGELOG.md` with structured entries | **Manual CHANGELOG** |
| Conventional commits without a changelog file | **Commit-driven** — the git log is the changelog |
| `RELEASES.md` or `HISTORY.md` | **Manual release notes** |

Note which mechanism applies — the rest of the procedure adapts accordingly.

### 2. Read inputs

- **Version manifest** — the file that holds the current version:
  - Node.js: `package.json` → `version`, `private`, `name`
  - Rust: `Cargo.toml` → `[package] version`
  - Python: `pyproject.toml` → `[project] version` or `__version__` in `__init__.py`
  - Other: identify the canonical version source
- **Pending change entries** — depends on mechanism detected above:
  - Changesets: `.changeset/*.md` (excluding `README.md` and `config.json`)
  - towncrier: `changelog.d/*.{bugfix,feature,breaking,...}`
  - Manual: inspect `CHANGELOG.md` for an `[Unreleased]` section
  - Commit-driven: commits since the last tag (`git log <last-tag>..HEAD`)
- **Previous releases** — `CHANGELOG.md` or `git tag --sort=-version:refname` for stylistic continuity.

### 3. Compute pending bump

Aggregate pending changes by severity:
- Any breaking/major → proposed bump is **major**
- Else any new feature/minor → proposed bump is **minor**
- Else any fix/patch → proposed bump is **patch**
- Else → nothing pending, **release is not due**

For Changesets, read the frontmatter level field:
```
---
"<package-name>": minor
---
```

Compute the proposed version by applying the bump. Semver pre-1.0 rule: in `0.x.y`, breaking changes ride the `x` (minor) bump — they do not require a major bump.

### 4. Decide: is the release DUE?

| State | Decision |
|---|---|
| No pending changes | **Not due** — done, early exit |
| Pending + pre-release / `private` + proposed version still in `0.0.x` range | **Not due yet** — pre-feature; surface the proposal as a heads-up |
| Pending + pre-release / `private` + proposed version is `0.1.0+` | **Due if the headline feature is in** — present the proposal, ask the user |
| Pending + public package + any `major` | **Due now** |
| Pending + public package + ≥ 1 `minor` or ≥ 3 `patch` | **Due** — propose to ship |
| Pending + public package + < 3 `patch` only | **Soft due** — propose but flag it could wait |

These are heuristics. A single security-fix patch ships immediately; ten cosmetic patches probably batch.

### 5. If DUE, draft the value-focused CHANGELOG entry

**This is the part that takes care.** Tooling-generated output inherits the raw change-entry text directly — it is often terse and leans technical. Rewrite it before commit.

The model is **Valve's Dota 2 patch notes** as actually published. The reader is the consumer of the package, not its author. They want: "what can I do now that I couldn't before, and how does my code need to change?"

#### Style

**Section headers — Title Case.** Examples from Valve: "General Mechanics", "Hero Adjustments", "Bug Fixes". Adapt to your package:

- `## General` — top-level capabilities and breaking changes
- `## Public API` — new exports, signature changes, deprecations
- `## Behaviour` — things that work differently without an API change
- `## Performance` — measurable wins the user will notice
- `## Bug Fixes` — terminal section, purely factual

Skip a section entirely if it has nothing in it.

**Per-entry shape — bold anchor + colon + delta.** Valve's canonical pattern:

```
- **Bloodstone**: spell lifesteal 30% → 20%.
- **Anti-Mage**: major rework — new innate applies movement-speed slow.
```

For a library, the anchor is the symbol the user calls:

```
- **`Session.run()`**: now returns a frozen `Transcript` instead of
  a plain object. `turns` and `finalScene` are where they were.
- **`RangeError`**: carries `.attempted` and `.available` for typed
  handling without parsing `.message`.
```

**Use `→` for numerical or behavioural deltas.** `"Cooldown 7s → 18s"`, `"Coverage threshold 80% → 75%"`.

**Tense — declarative, present, sentence fragments.** "Sessions now expose …" not "Added event emission …".

**What goes in:**
- Concrete user-callable changes (new exports, behaviour shifts, error-shape changes)
- Numerical deltas with `→`
- Breaking changes with a one-line migration hint when non-obvious
- Bug fixes the user might have hit (terminal `## Bug Fixes` section, factual)

**What stays out:**
- Internal refactors that don't change behaviour
- Build/lockfile/lint config changes
- Test framework migrations
- PR numbers, SHAs, branch names
- The *why* — unless it's a security fix or a breaking-change rationale the user needs

#### Good vs bad

✅ Value-focused (what the user reads):

```markdown
## 0.2.0 — YYYY-MM-DD

One-line summary of what this release unlocks.

### Public API

- **`Client.query()`**: now accepts an optional `timeout` parameter;
  defaults to 30s (was infinite). Pass `timeout: 0` to restore
  previous behaviour.
- **`AuthError`**: carries `.statusCode` and `.retryAfter` for
  typed handling without parsing `.message`.

### Bug Fixes

- Fixed a race condition in the connection pool that could cause
  duplicate requests under high concurrency.
```

❌ Engineering changelog (what tooling generates verbatim — do NOT ship):

```markdown
## 0.2.0

- Added timeout parameter to query method
- Refactored AuthError to carry statusCode field
- Fixed race condition (see PR #142)
- Bumped eslint peer range
- Migrated tests from mocha to vitest
```

### 6. Present the proposal

```
Release check: DUE / NOT DUE / SOFT-DUE
Current version: x.y.z   →   Proposed: x.y.z

Pending changes (N):
  - <entry>   <level>   <one-line summary>

Proposed CHANGELOG entry:
  [draft here]

Action plan:
  1. Run the project's version-bump command:
       Changesets:  pnpm changeset version  (or npx changeset version)
       towncrier:   towncrier build --version x.y.z
       Manual:      edit version manifest + CHANGELOG.md directly
  2. Overwrite the generated CHANGELOG entry with the rewrite above.
  3. Run the project's verification gate (tests, lint, build).
  4. Commit with message matching the project's convention (e.g. "🔖 release: vX.Y.Z").
  5. Tag: git tag vX.Y.Z
  6. Push: git push origin <main-branch> --follow-tags
  7. If the project has a publish workflow (npm publish, cargo publish, PyPI, CI release action),
     trigger it — or note that it runs automatically on tag push.

Approve to proceed?
```

If NOT DUE:

```
Release check: not due. <one-line reason>.
Pending: N change entries, would propose vX.Y.Z when ready.
```

### 7. On approval, execute the plan

Run the steps in order. After each, verify the previous step succeeded. If the version-bump command fails or produces unexpected output, stop and surface — do not silently push.

For the CHANGELOG rewrite specifically:
1. Capture the auto-generated entry as a reference (do **not** ship it).
2. Replace that block with the value-focused rewrite.
3. Run the project's verification gate.
4. Stage and commit.
5. Tag and push with `--follow-tags`.

## Anti-patterns

- **Don't release just because change entries exist.** A single typo-fix for a private package isn't a release event.
- **Don't write the changelog from the diff.** Write from intent — read the change entries and commit bodies, then translate to what the user *gains*.
- **Don't ship the auto-generated CHANGELOG without rewriting.** Tooling output is a starting point, not a final product.
- **Don't bypass the user's approval for the actual release.** Propose, wait, then act. Releases are public and hard to reverse.
- **Don't add a section that's empty.** Skip `## Bug Fixes` if there are no fixes.

## Cross-references

- `/staleness-audit` runs *before* the commit. This check runs *after* the commit lands, since release decisions depend on the version manifest + change-entry state post-commit.
- Valve's Dota 2 patch notes: <https://www.dota2.com/news/updates> — the canonical reference for the changelog style this skill enforces.

## Why this exists

A project's CHANGELOG is the first thing a prospective user reads after the README. Release tooling makes it easy to *generate* one and easy to write a bad one — the default flow stitches together author-written summaries verbatim, which often read like a git log. Valve's Dota patch notes are the canonical example of how to write a changelog the audience actually wants: every line is a thing the player can observe, not a thing the engineers did. Same principle: the user wants to know what they can do now, what they need to update, and what bugs they no longer have. Nothing else.
