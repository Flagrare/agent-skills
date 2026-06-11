# Research: Kent Dodds' testing philosophy, generalized across languages and layers

- **Slug:** `2026-06-11-kent-dodds-testing-philosophy`
- **Date:** 2026-06-11
- **Status:** complete
- **Triggered by:** Operator report that test-proposing/reviewing skills (`/flagrare:atdd-plan`, `/flagrare:implementation-review`) under-emphasise the necessity of end-to-end tests and aren't aggressive enough at catching tests that assert implementation details instead of behavior. Goal: ground the fix in Kent Dodds' primary writing and generalize it beyond JS/React to any language and any layer (frontend, backend, CLI, library).
- **Informed:** [`/flagrare:testing-philosophy`](../../plugins/flagrare/skills/testing-philosophy/SKILL.md) (new shared reference skill), [`/flagrare:atdd-plan`](../../plugins/flagrare/skills/atdd-plan/SKILL.md) (e2e floor + sharper AT rules), [`/flagrare:implementation-review`](../../plugins/flagrare/skills/implementation-review/SKILL.md) (e2e-gap check + sharpened Check 4), [`/flagrare:tdd-writer`](../../plugins/flagrare/skills/tdd-writer/SKILL.md) and [`/flagrare:wrap-up`](../../plugins/flagrare/skills/wrap-up/SKILL.md) (cross-refs).

## Question

What does Kent Dodds actually argue about (a) the role and necessity of end-to-end tests within the Testing Trophy, and (b) testing behavior over implementation details — and how do those arguments translate, without loss, into languages and layers other than the JavaScript/React frontend context he writes from?

## Sources

### [Testing Implementation Details](https://kentcdodds.com/blog/testing-implementation-details)
- **Authors / Org:** Kent C. Dodds
- **Type:** engineering blog (primary)
- **Published:** 2018 (updated since); **Accessed:** 2026-06-11
- **Relevance:** high
- **What this contributed:** The core of the "behavior over implementation" pillar — the definition of an implementation detail, the two concrete failure modes (false negatives on refactor, false positives that pass while the app is broken), the "tests as an unwanted third user" framing, and a concrete list of what counts as an implementation detail.
- **Quoted:**
  > "Implementation details are things which users of your code will not typically use, see, or even know about."

  > "Tests which test implementation details can give you a false negative when you refactor your code. And they can give you a false positive when your application breaks."

  > "by making our test use the component differently than end-users and developers do, we create a third user our application code needs to consider: the tests!"

### [The Testing Trophy and Testing Classifications](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- **Authors / Org:** Kent C. Dodds
- **Type:** engineering blog (primary)
- **Published:** 2021; **Accessed:** 2026-06-11
- **Relevance:** high
- **What this contributed:** The four-layer model (static / unit / integration / e2e), the definition of e2e as "as little mocking as possible," the confidence-vs-cost ("return on investment where return is confidence and investment is time") framing, and the rationale for integration-heavy testing.
- **Quoted:**
  > "End to End: ... the place where you attempt to validate that things work without any (or more practically 'as little as possible') mocking in place."

  > "The more your tests resemble the way your software is used, the more confidence they can give you." (the guiding principle, attributed to Dodds, 2018)

### [Write tests. Not too many. Mostly integration.](https://kentcdodds.com/blog/write-tests) (via on-site search summary)
- **Authors / Org:** Kent C. Dodds (phrase originated in a tweet by Guillermo Rauch)
- **Type:** engineering blog (secondary here — used the search summary, not a full fetch)
- **Published:** 2019; **Accessed:** 2026-06-11
- **Relevance:** medium
- **What this contributed:** The headline doctrine and the reason integration is the default tier (best confidence-per-effort trade-off). Confirmed the Test Pyramid has given way to integration-over-unit as conventional wisdom.

## Synthesis

Two pillars, both reducible to one principle.

**The one principle:** *"The more your tests resemble the way your software is used, the more confidence they can give you."* Every other rule is a corollary. It is intrinsically language- and layer-agnostic — "the way your software is used" just resolves to a different surface per context.

### Pillar 1 — Behavior over implementation details

An **implementation detail** is anything the users of your code will not use, see, or know about. Tests that bind to implementation details fail in two ways at once: they cry wolf when you refactor without changing behavior (false negative), and they stay green when you actually break the behavior (false positive). A test coupled to internals is a *third user* of your code that nobody asked for — you now have to keep the end user, the calling developer, and the test all happy.

The fix is to assert only on what a real user can observe, and to drive the code only through the surface a real user touches. "User" generalizes cleanly:

| Layer | The "user" | Observable surface to assert on | Implementation details to NOT touch |
|---|---|---|---|
| Library / module | The calling developer | Return values, thrown errors, public types, emitted events | Private fields/methods, internal helpers, internal data structure choices |
| Backend / API | The HTTP/RPC client | Status codes, response bodies, headers, persisted state visible via the API, emitted domain events | ORM internals, service-layer method names, query shapes, internal DTOs |
| Frontend / UI | The person clicking | Rendered text, roles, what appears/disappears after an interaction | Component state variables, hook internals, CSS class names, child-component names |
| CLI | The person at the prompt | stdout/stderr, exit code, files written | Internal flag parsing, function call order |

Concrete tells of an implementation-detail test, regardless of stack:
- It asserts on private fields, unexported functions, internal state, or internal data-structure shape.
- It asserts that a particular internal method/function *was called* (mock call-count / spy assertions on types you own).
- It mocks a collaborator you own rather than only mocking at a true external boundary (network, disk, clock, OS process, third-party service).
- It would break under a behavior-preserving rename or internal restructure. (The acid test: "if I refactor internals but keep the contract, does this test break? If yes, it's testing the wrong thing.")
- Its name describes a mechanism (`calls setIndex with 0`) rather than a behavior (`shows the first slide on load`).

### Pillar 2 — The Testing Trophy, and where e2e is genuinely necessary

Four layers, bottom to top: **static** (types + lint — free correctness), **unit** (a piece in isolation, dependencies mocked), **integration** (several units working together — the default, best confidence-per-effort), **e2e** (the whole system with as little mocking as possible). Height = confidence; height also = cost/time. The doctrine "write tests, not too many, mostly integration" is about spending most effort in the middle.

Crucially, "mostly integration" is **not** "skip e2e." The operator's complaint is the common misreading. Two failure directions exist and both are violations:
- **Too much e2e** — every scenario duplicated as a slow, flaky full-stack test that could be an integration test. (atdd-plan/implementation-review already guard this direction.)
- **No e2e at all for the critical path** — a user-facing flow where every layer is tested in isolation but nothing proves they connect. This is the under-guarded direction and the one the operator flagged.

The generalized rule: **every user-facing application should have at least one end-to-end (or as-high-as-practical) test that exercises its most critical happy path through the real, assembled system.** "E2e" itself generalizes — it does not require a browser:
- Frontend app → browser-driven test of the critical user journey (load → act → see result).
- Backend service → a test that hits the real running service over HTTP against a real (test) database, asserting on the response and persisted state.
- CLI → invoke the built binary as a subprocess, assert on stdout/exit code/filesystem effects.
- Library → the "e2e" is consuming the published public API exactly as a downstream user would, with nothing internal stubbed.

How many: one or two critical paths, not one per scenario. The e2e tier proves the wiring; integration proves the behavior; unit proves the tricky pure logic; static proves the shapes. A plan or review that omits the wiring proof for a user-facing feature has a gap, even if unit and integration coverage look complete.

### Bottom line for the skills

Test-proposing and test-reviewing skills should enforce, language- and layer-agnostically:
1. **Necessity of e2e** — flag any user-facing/critical feature that lacks at least one full-stack/e2e (or highest-practical) test of its happy path; keep the existing guard against e2e *overuse* so both directions are covered.
2. **Behavior over implementation** — flag the concrete tells above (private-state assertions, spy-on-owned-collaborator, mock-call-count, refactor-fragile, mechanism-named tests), framed as "would this break under a behavior-preserving refactor?" and "does this assert what a real user observes?".
3. Anchor both to the single principle: *tests should resemble how the software is actually used.*

## Downstream uses

- `/flagrare:testing-philosophy` — new shared reference skill; the single, layer-agnostic source of truth (the one principle, both pillars, the per-layer user table, the e2e generalization table).
- `/flagrare:atdd-plan` — REQUIRED-BACKGROUND cross-ref; Acceptance Tests now require an e2e/full-stack happy-path test for user-facing work; refuse-list sharpened with the implementation-detail tells and acid test.
- `/flagrare:implementation-review` — Check 2 gains the e2e-coverage gap check; Check 4 gains the two acid tests, the spy/mock-call-count tell, and both-direction Trophy-shape checks.
- `/flagrare:tdd-writer` — Testing-section guidance points to the philosophy and the e2e floor.
- `/flagrare:wrap-up` — notes that test quality is owned by the philosophy via implementation-review Checks 2–4.
- `smoke-test` / `bug-bash` — not wired: they already *are* e2e/behavior verification (driving a real running system as a user), so they embody the philosophy rather than propose/review tests.
