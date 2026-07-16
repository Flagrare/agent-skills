# Security audit skill

> No em-dashes in this document (repo hook enforces it in generated `.md`).

Named `security-audit` (not `security-review`) to avoid selection confusion with Claude
Code's built-in `/security-review` command. The name matches the collection's existing
`staleness-audit` and `ux-audit`.

## Problem

Security review exists today only as a shallow sub-check: Subagent 2 in `pr-reviewer`
(OWASP Top 10 on a PR diff) and, loosely, correctness-adjacent checks in
`implementation-review`. Both are deliberately thin and compete for attention with four to
five sibling checks. There is no dedicated depth pass and no single source of security truth
the gates can reference.

## Shape

Mirror the proven pattern already in the repo: Checks 2 to 4 of `implementation-review` do not
inline their own test philosophy, they pull in the `testing-philosophy` skill so every gate
judges against one definition. Security works the same way.

1. **New `security-audit` skill** holds the depth (threat taxonomy, discipline, finding
   format, generic dependency audit). Standalone-invocable as `/flagrare:security-audit`.
2. **`implementation-review` gains Check 7 (Security)**, a seventh parallel subagent whose
   brief pulls in the `security-audit` content, exactly like Checks 2 to 4 pull in
   `testing-philosophy`.

One source of security truth, referenced from every gate that needs it. `pr-reviewer`'s
Subagent 2 can later reference the same skill instead of duplicating a weaker list.

## `security-audit` skill

**Threat taxonomy:**

1. Injection: SQL, command, XSS, template, path traversal
2. Broken authn/authz: missing checks, IDOR / tenant-leak (the 403-vs-404 case), privilege
   escalation
3. Secrets and sensitive-data exposure: hardcoded keys, secrets in logs, PII leakage
4. Input validation at trust boundaries: every untrusted-to-trusted crossing
5. SSRF and unsafe outbound requests
6. Insecure deserialization and unsafe reflection
7. Crypto misuse: weak password hashing, `Math.random()` for tokens, static IV, ECB
8. Dependency CVEs: when a lockfile moved, detect the package manager generically and run its
   auditor, degrading gracefully when the tool is absent

**Generic dependency audit** (detect from lockfile / manifest, run, degrade gracefully):

| Ecosystem | Detect | Command |
|---|---|---|
| npm / pnpm / yarn | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock` | `npm audit` / `pnpm audit` / `yarn npm audit` |
| Python | `poetry.lock`, `requirements*.txt`, `uv.lock` | `pip-audit` |
| Rust | `Cargo.lock` | `cargo audit` |
| Go | `go.sum` | `govulncheck ./...` |
| Ruby | `Gemfile.lock` | `bundle audit` |
| PHP | `composer.lock` | `composer audit` |

If the auditor is not installed, do not fail: flag "lockfile moved, run your dependency
auditor" and name the added or bumped packages from the diff.

**Discipline:** every finding needs a concrete exploit path and a fix, then a confidence score
(borrowed from the built-in `code-review` command's 0-100 rubric). Low-confidence, theoretical
findings are dropped, not reported. Default scope is the diff, but review follows the trust
boundary: a one-line change to an auth check pulls in the surrounding auth path, not just the
changed line.

**Finding format** matches the house style: `✓ clean | ⚠ finding | ✗ blocking finding`, with
`file:line`, the exploit path, and the fix.

## `implementation-review` changes

- Frontmatter description: "Six checks" becomes seven; add security to the list.
- Intro and Step 2: "all six" becomes "all seven"; spawn seven subagents in parallel.
- New **Check 7 · Security** subagent brief. Inputs: full `git diff --staged`, file list,
  lockfile diff. Brief pulls in the `security-audit` skill content. In the commit gate the
  dependency audit stays scoped to deps the diff touched (fast, non-noisy); the full-tree audit
  is what the standalone run does.
- Step 3 synthesis format gains a Check 7 block.
- Anti-patterns: note security is diff-scoped-plus-trust-boundary, and do not report a
  theoretical finding without a concrete exploit path.

## Housekeeping

README goes from twenty-six skills to twenty-seven (both the count and the skill list).

## Inspiration from the built-in `/security-review`

Claude Code ships a `/security-review` command (a prompt compiled into the CLI binary, not a
readable file). We extracted its text and folded in the parts worth keeping:

- The >80% confidence gate and the 0.7-to-1.0 confidence rubric (below 0.7, do not report).
- The three-phase methodology: understand the repo's security model, compare the change
  against it, trace data flow from source to sink.
- The false-positive precedents list: client-side auth is not a vuln, React/Angular are
  XSS-safe without `dangerouslySetInnerHTML`, SSRF needs host/protocol control, env vars and
  CLI flags are trusted, test files and docs are out of scope, no memory-safety findings in
  memory-safe languages.
- The finding shape: file, line, severity, category, description, exploit scenario, fix.

Deliberate divergence: the built-in excludes dependency CVEs ("managed separately"); we keep
them as a separate deterministic audit step because the user asked for it and it is cheap.

## Non-goals

- Not a whole-app pentest harness. Diff-and-trust-boundary scoped.
- Not wired into `pr-reviewer` in this change (that reference is a later follow-on).
