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

### 6. Sync version-referencing files

A release bump touches more than the version manifest. Several files in a typical repo cite the current version, and they go stale the moment you tag the new one. Sweep for drift before presenting the proposal.

Common files to check:

| File | What to update | Pattern |
|---|---|---|
| `CITATION.cff` | `version:` field, optionally `date-released:` | Must match new package version exactly. GitHub's "Cite this repository" button reads this. |
| `SECURITY.md` | Supported-versions table | Bump the supported row; remove rows now out of support. |
| `README.md` | Any "Current version: vX.Y.Z" line; any status framing tied to the version (e.g. "vX.Y.Z is a research-grade preview") | Update version number; reconsider status framing if maturity actually shifted. |
| `CONTRIBUTING.md`, guides, architecture docs | Any "v0.X onwards" or "as of v0.X" claim that's now older than current | Bump or convert to a historical reference. |
| `pyproject.toml` / `package.json` / per-crate `Cargo.toml` | `version =` field if separate from workspace manifest | Match. |
| `docs/positioning/*.md`, `docs/research-log.md` | Any "Status: vX" line | Bump if it's meant to track current. |

How to find drift mechanically:

```bash
# Replace OLD with the version the release is moving past.
OLD="0.7.0"
grep -rn "v${OLD}\|version.*${OLD}\|\"${OLD}\"" \
  --include="*.md" --include="*.cff" --include="*.toml" \
  --include="*.yml" --include="*.yaml" \
  --exclude-dir=target --exclude-dir=node_modules --exclude-dir=.venv .
```

For each hit, judge:

- **Historical reference** ("v0.7.0 introduced X", "added in v0.7.0", "retracted in v0.5") — leave alone. These document what shipped, when. Bumping them rewrites history.
- **Current-version claim** ("TardigradeDB v0.7.0 is a research-grade preview", "Supported: 0.7.x", `version: "0.7.0"` in CITATION.cff) — update. These should track HEAD.

Community Standards files deserve special attention since they're the project's public face beyond the README:

- `CITATION.cff` — always bump.
- `SECURITY.md` — bump supported versions; if a previously-supported minor falls out of support, surface it in the CHANGELOG entry (consumers on the old minor need to know).
- `CODE_OF_CONDUCT.md` — usually no version coupling; verify the contact route is still valid.
- Any new community files added since the last release — call them out in the CHANGELOG entry as `### Community Standards`.

Include the doc updates in the same release commit. A two-commit release ("bump version" + "update docs") splits the artifact across two SHAs and makes `git blame` on `CITATION.cff` lag the actual release date.

**Skip this step only for trivial patch releases** (e.g. a single typo fix) where the only version-coupled file is the manifest. Anything user-visible — and any release of meaningful scope — gets the full sweep.

### 7. Present the proposal

```
Release check: DUE / NOT DUE / SOFT-DUE
Current version: x.y.z   →   Proposed: x.y.z

Pending changes (N):
  - <entry>   <level>   <one-line summary>

Proposed CHANGELOG entry:
  [draft here]

Documentation drift to fix in the same commit (from step 6):
  - <file>:<line>   <one-line description>
  - …

Action plan:
  1. Run the project's version-bump command:
       Changesets:  pnpm changeset version  (or npx changeset version)
       towncrier:   towncrier build --version x.y.z
       Manual:      edit version manifest + CHANGELOG.md directly
  2. Overwrite the generated CHANGELOG entry with the rewrite above.
  3. Apply the documentation drift fixes from step 6 (CITATION.cff,
     SECURITY.md supported-versions, README status line, etc.).
  4. Run the project's verification gate (tests, lint, build).
  5. Commit with message matching the project's convention (e.g. "🔖 release: vX.Y.Z").
  6. Tag the release commit explicitly (NOT main):
       git tag vX.Y.Z <release-commit-sha>
     The tag MUST point at the commit that bumped the version manifest.
     If you tag main and main has moved past the release commit, the
     publish workflow will check out the wrong tree and build wheels
     with the previous version — PyPI / crates.io will then reject
     them as duplicates. (See the "GitHub Release vs tag commit"
     section below for why this matters.)
  7. Push: git push origin <main-branch> --follow-tags
  8. If the project has a publish workflow (npm publish, cargo publish, PyPI, CI release action),
     trigger it — or note that it runs automatically on tag push or
     release publish.
  9. **Verify the publish actually succeeded.** Tagging is not shipping.
     For GitHub Actions release workflows:
       gh run list --workflow=<publish-workflow>.yml --limit 1
     If status is `failure` or `cancelled`, inspect with `gh run view
     <id> --log-failed` and surface the root cause before declaring
     the release done. Common failure: wheel filename version doesn't
     match the tag (see "GitHub Release vs tag commit" below).
 10. **Confirm the artifact actually landed in the index.** Tooling
     can succeed-then-silently-skip. For PyPI:
       curl -s https://pypi.org/pypi/<package>/json | jq -r .info.version
     For crates.io:
       cargo search <crate> --limit 1
     For npm:
       npm view <pkg> version
     If the latest published version is still the previous one after
     the workflow reports success, something between the workflow and
     the registry broke — escalate, don't move on.

Approve to proceed?
```

### GitHub Release vs tag commit — the silent-publish-failure trap

GitHub Actions workflows triggered by `on: release: [published]` check
out the **release's target commit**, not the **git tag's commit**.
These can diverge in three common ways:

1. **Release created from a stale main.** Operator clicks "Draft a new
   release" in the GitHub UI, picks tag `vX.Y.Z`, but the release's
   "target" defaults to main — which may be ahead of (or behind) the
   tagged commit. The workflow checks out main, not the tag.
2. **Tag pushed before version bump.** Operator runs `git tag vX.Y.Z`
   on a commit that doesn't bump the version manifest, then bumps it
   in a follow-up commit. The tag is wrong; the workflow builds the
   pre-bump tree.
3. **Multiple consecutive releases without main rebasing.** Operator
   tags v0.6.0 and v0.7.0 within minutes on commits that all share a
   stale Cargo.toml because the version-bump commits haven't been
   reordered correctly.

All three produce the same downstream failure: the wheel/crate/package
filename carries the *old* version, the registry rejects it as a
duplicate of the previously-shipped release, and the workflow status
turns red. Recovery requires either re-tagging (if the registry hasn't
seen any artifact yet) or bumping past the gap (if a partial upload
landed first).

**Prevention checklist before pushing the tag:**

- `git show <tag>:<manifest>` matches the expected new version.
  Example: `git show v0.7.2:Cargo.toml | grep '^version'` returns
  `version = "0.7.2"`.
- The GitHub Release (if created via UI) points at the same commit
  the tag points at. If using `gh release create vX.Y.Z`, this is
  automatic. If using the UI, the "Target" dropdown must be the
  tagged commit, not main.
- The publish workflow's first step asserts wheel-version-matches-tag
  before uploading. Add this guard if it's missing:
  ```yaml
  - name: Verify wheel version matches tag
    run: |
      EXPECTED="${GITHUB_REF#refs/tags/v}"
      for whl in dist/*.whl; do
        VER=$(echo "$whl" | sed -E 's/.*-([0-9]+\.[0-9]+\.[0-9]+)-.*/\1/')
        [ "$VER" = "$EXPECTED" ] || { echo "wheel $whl version $VER != tag $EXPECTED"; exit 1; }
      done
  ```
  This converts a silent PyPI 400 into a loud workflow failure at the
  build stage, where the diagnostic message is actionable.

If the project has had a publish failure of this shape before, surface
it in the release proposal as a known-risk reminder: *"v0.7.0 / v0.6.0
both failed PyPI publish due to GitHub-Release-vs-tag-commit drift;
verifying tag commit matches release target before push."*

If NOT DUE:

```
Release check: not due. <one-line reason>.
Pending: N change entries, would propose vX.Y.Z when ready.
```

### 8. On approval, execute the plan

Run the steps in order. After each, verify the previous step succeeded. If the version-bump command fails or produces unexpected output, stop and surface — do not silently push.

For the CHANGELOG rewrite specifically:
1. Capture the auto-generated entry as a reference (do **not** ship it).
2. Replace that block with the value-focused rewrite.
3. Run the project's verification gate.
4. Stage and commit.
5. Tag the release commit explicitly (`git tag vX.Y.Z <release-sha>`),
   not whatever HEAD happens to be — see "GitHub Release vs tag commit"
   in step 7.
6. Push with `--follow-tags`.
7. Verify the publish workflow succeeded (`gh run list --workflow=<…>
   --limit 1`) and that the artifact landed in the registry (PyPI /
   crates.io / npm) before declaring done. A green tag-push is not a
   green release.

## Anti-patterns

- **Don't release just because change entries exist.** A single typo-fix for a private package isn't a release event.
- **Don't write the changelog from the diff.** Write from intent — read the change entries and commit bodies, then translate to what the user *gains*.
- **Don't ship the auto-generated CHANGELOG without rewriting.** Tooling output is a starting point, not a final product.
- **Don't bypass the user's approval for the actual release.** Propose, wait, then act. Releases are public and hard to reverse.
- **Don't add a section that's empty.** Skip `## Bug Fixes` if there are no fixes.
- **Don't declare a release done at the tag push.** Tagging is necessary, not sufficient. Verify the publish workflow ran green AND the artifact actually appears in the registry. A "tag pushed, must be live" assumption is how multi-release publish failures stack up unnoticed — the only signal that something's wrong is when a downstream consumer reports `pip install <name>` returns the version-before-last.

## Cross-references

- `/staleness-audit` runs *before* the commit. This check runs *after* the commit lands, since release decisions depend on the version manifest + change-entry state post-commit.
- Valve's Dota 2 patch notes: <https://www.dota2.com/news/updates> — the canonical reference for the changelog style this skill enforces.

## Why this exists

A project's CHANGELOG is the first thing a prospective user reads after the README. Release tooling makes it easy to *generate* one and easy to write a bad one — the default flow stitches together author-written summaries verbatim, which often read like a git log. Valve's Dota patch notes are the canonical example of how to write a changelog the audience actually wants: every line is a thing the player can observe, not a thing the engineers did. Same principle: the user wants to know what they can do now, what they need to update, and what bugs they no longer have. Nothing else.
