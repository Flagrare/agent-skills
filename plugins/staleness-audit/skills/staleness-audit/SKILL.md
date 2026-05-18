---
name: staleness-audit
description: Pre-commit audit. Invoke before every git commit. Diffs the staged change against the repo's "canaries" (README, ADRs, roadmap, public API, changelogs, TSDoc, test discipline) and surfaces anything that's drifted out of sync. Updates the obvious drifts in place; flags judgement calls for the operator.
---

# Staleness audit

Run this before every commit. The goal is simple: **a commit should leave the docs, types, and roadmap in a state consistent with the code it ships**. Drift between code and its surrounding narrative is how projects rot.

Don't be lazy — actually run the checks. Each one is a `grep` or a `diff`. The whole audit should take under 30 seconds.

## How to invoke

You (the model) invoke this skill yourself, before staging the final commit. The user's binding rule (saved in agent memory) says: *every commit goes through this checklist*. If you're amending or splitting commits, run it per commit.

## Inputs

- `git diff --staged --stat` — what's about to be committed
- `git diff --staged` — the actual hunks (only read the ones you need)
- `git status` — what's unstaged or untracked that might also be drift
- The repo working tree for the canary files listed below

## Procedure

Work through the checks in order. For each finding, either **fix it now** (if the fix is mechanical and in scope) or **note it explicitly** in the commit body / the response to the user (if it's a judgement call).

### 1. README staleness

The `README.md` is the project's storefront. After every commit, ask:

- **Status line**: does `## Status` (or the equivalent line) still match reality? Words like "pre-alpha", "bootstrapping", "WIP", "coming soon", "not yet implemented" need to age out as features ship. If this commit moves the needle, update the status text.
- **Roadmap checkboxes**: `- [ ] X` for things that *just shipped* in this commit (or earlier ones not yet ticked) should become `- [x] X`. Conversely, anything ticked that's been ripped out needs to be re-opened or removed.
- **Code examples**: if a public-API signature changed (look at `src/index.ts` diff), do the README code blocks still compile and reflect the new shape? Grep the README for the renamed/removed identifier.
- **Badge accuracy**: if a CI workflow or license changed, the badges still point at the right thing.

### 2. ADR index integrity

`docs/decisions/README.md` is the index. Check:

- Any new `docs/decisions/NNNN-*.md` that isn't in the index table. Add it.
- Any ADR whose `Status:` says "Accepted" but is actually superseded by a later ADR — the older one should say `Accepted (X superseded by ADR-NNNN)` and the newer one should declare what it supersedes.
- ADR cross-references (`[ADR-0002](./0002-…)`) that point at filenames that no longer exist.

### 3. Public API ↔ barrel export sync

For a library, `src/index.ts` is the only thing consumers can `import`. After every commit that touches `src/`:

- For every `export` newly added in `src/**/*.ts` (other than `index.ts`), is it re-exported from `src/index.ts`?
- For every removed export, is the corresponding line in `src/index.ts` also removed?

Quick check: `grep -hE "^export " src/*.ts | grep -v index.ts | sort | uniq` versus the lines in `src/index.ts`.

### 4. TSDoc completeness on public surface

Per ADR-0002, every exported symbol needs TSDoc. Spot-check the staged `.ts` files:

- Any new `export class`, `export function`, `export interface`, `export type`, `export const` without a leading `/** ... */`?
- Any newly added public method on an exported class without a TSDoc?
- TSDoc that still says "TODO" or "@todo"?

(`eslint-plugin-tsdoc` enforces *syntax*; this check enforces *presence*.)

### 5. Changeset for user-facing changes

If the commit touches `src/`, ask: is this user-observable?

- If yes and there's no `.changeset/*.md` (other than `README.md`) in this commit, write one. Use `pnpm changeset` to draft.
- If no (pure internal refactor / test / docs / tooling), no changeset is needed — but note that explicitly in the response.

### 6. CONTRIBUTING and docs/decisions hygiene

- Search `CONTRIBUTING.md` for any reference to removed tooling (`cucumber`, `gherkin`, `attw`, etc. — anything that's not in `package.json` anymore).
- If a workflow changed (lefthook hook, CI job, npm script), make sure CONTRIBUTING reflects it.

### 7. Test name discipline (Kent-style)

Per ADR-0003 + the testing-philosophy memory, test names should describe **behaviour**, not method names. Grep newly added/changed test files for:

- `it("works")`, `it("test \d")`, `it("it should")`, `it("returns the value")` — vague or method-centric. Flag.
- Good names look like `it("rejects an out-of-range choice index with StoryChoiceRangeError")`.

### 8. Stale markers in new code

Grep the staged diff for tokens that shouldn't ship:

- `TODO`, `FIXME`, `XXX`, `HACK`, `@todo` — fine if they reference an issue (`TODO(#42)`); not fine if naked.
- `console.log`, `debugger`, `.only`, `.skip` in test files.
- Leftover `// biome-ignore`, `// eslint-disable` without an explanation comment.

### 9. Memory file crosslinks

The `~/.claude/projects/-home-flagrare-Dev-poltergink/memory/` directory uses `[[name]]` to crosslink. If a commit touches docs that reference memory, or memory itself, check:

- Every `[[some-name]]` resolves to a file `some-name.md` in the memory dir.
- The `MEMORY.md` index has an entry for every `.md` file (other than itself).

### 10. Commit message itself

Before invoking `git commit`, verify the message:

- Leading **gitmoji** present (✨ 🐛 📝 ♻️ 🧪 ⚡ 🧹 🔧 🔖) — required.
- `type(scope): subject` shape — required.
- Subject is a **tight topical noun phrase**, not an imperative sentence. Target ≤ 50 chars.
- Body explains *why* and lists what changed at file level when useful.

### 11. Automated-committer message format

The commitlint rule applies to **every** commit that hits this repo — including ones produced by tools like Changesets, Renovate, Dependabot, or release bots. Their default messages are *not* gitmoji-formatted. Whenever a commit you're staging touches a workflow or config that controls an automated committer, audit the messages it produces:

- `.github/workflows/release.yml` — `changesets/action`'s `commit:` and `title:` inputs.
- `.github/renovate.json` — `commitMessagePrefix` / `semanticCommits` (we set `semanticCommits` + `semanticCommitTypeAll(chore)` so the PR gets `chore:` prefix, but the *commit messages* on Renovate's PR branches need to comply once squash-merged).
- `.github/dependabot.yml` — `commit-message.prefix` (currently `chore`).
- Any new GitHub Action or bot that commits on the project's behalf.

The rule of thumb: if a tool can push a commit, configure its commit-message template to satisfy commitlint *or* arrange for the commits to be squash-merged with a manually-written message.

### 12. CI workflow drift

Whenever this commit touches `.github/workflows/*.yml`:

- Sanity-check there's no version conflict between an action's `with:` inputs and a config file in the repo (e.g. `pnpm/action-setup`'s `version:` vs. `package.json#packageManager`). This bit us in `🐛 fix(ci): pnpm version conflict`.
- Confirm any action version pins (`actions/checkout@v4` etc.) still match what's running elsewhere in `.github/workflows/`.
- If a job's prerequisite tool was removed from the repo (e.g. cucumber, attw), the corresponding workflow step should go in the same commit.

## Output

When you're done, give the user a concise audit line for each check — `✓` if clean, `→ fixed: …` if you applied a mechanical fix, `⚠ needs decision: …` if it's a judgement call. Don't pad with checks that found nothing — just say "Clean: README, ADR index, exports, TSDoc, changeset N/A, contributing, test names, markers, memory, automated-committer, workflow drift" if everything passes.

If any check found a real issue, *fix it before committing* unless the user explicitly opted out of fixing this round.

## Anti-patterns (what this skill is not)

- It is not a substitute for `pnpm verify`. The pre-push hook still runs the full quality gate.
- It is not a place to add new tests or refactors — those belong in the commit they relate to.
- It is not a license to chase every TODO across the repo — only the drift caused or revealed by *this* commit.

## After this skill: invoke `/release-check`

Once the commit lands, invoke `/release-check` immediately. That skill answers the post-commit question "is a release due?" using the `.changeset/` state and `package.json#private`, and drafts a value-focused CHANGELOG entry (Valve Dota style) when one is. Cheap when nothing's pending.

## Why this exists

Project rot starts when README says "pre-alpha" three months after v1.0, when ADR-0001 still says "Accepted" while the codebase has moved on, when the roadmap shows boxes already ticked elsewhere. Catching drift at commit time costs ~30 seconds. Catching it at "why is our README lying" time costs hours and credibility. See also the `feedback-pre-commit-staleness-audit` memory entry that mandates running this skill before every commit.
