# Backend smoke test: priorities and tooling

This is what gets exercised in the priority loop when the domain is `backend` (or the backend branch of `both`). The main SKILL.md describes the loop; this file describes what each priority tier actually checks.

The priority order is dependency-ordered: a failure at a lower tier means tiers above it are noise until the failure is fixed. Don't reorder.

---

## Tooling

Pick whatever the project already uses. Don't introduce a new test framework for a smoke pass.

- **HTTP service**: the project's existing test framework with an HTTP client (`pytest` + `httpx`, `vitest`/`jest` + `supertest`, `cargo test` + `reqwest`, `go test` + `httptest`).
- **gRPC service**: framework-native client; `grpcurl` for ad-hoc verification during the loop.
- **Worker / job**: invoke the handler with a test message; assert the side effects (DB row written, downstream call made, ack emitted).
- **Contract validation**: against the project's existing OpenAPI / GraphQL schema / proto if it has one. If not, derive expected contract from the handler signature and assert against that, but flag the absence, long-term, schema-as-source-of-truth is the right move.

Run against the same instance the dev would run locally, usually `localhost:<port>` with a dev DB seeded by fixtures. If the feature requires staging (e.g., it integrates with a third-party service that has no local emulator), run against staging but isolate test data with a tenant prefix the loop creates and tears down.

---

## P0: Reachability (fail fast, seconds)

The "is the service even alive" tier. If P0 fails, fix it first; everything after is noise.

- The service responds on its expected port and base URL.
- Health endpoint returns 2xx (`/healthz`, `/health`, `/-/health`, whatever the project uses).
- Required env vars are set (the service didn't boot half-configured and silently 500).
- Required downstream dependencies are reachable from the service (DB connection, message broker, cache).

A P0 failure typically means config drift, a missing migration, or an env var that the dev forgot to copy. Diagnose at the lowest layer, config or boot logs, not the application code.

---

## P1: Acceptance criteria (the headline)

Every acceptance criterion from the brief becomes one scenario. Each is exercised against a real running instance, not a unit test with mocks.

- One assertion per AC. If the AC says "returns the user's tickets sorted by created_at desc", the scenario verifies both the response shape and the order.
- Use real data flows. Seeding a row directly via the DB to skip the create endpoint defeats the purpose, drive the create endpoint, then the read endpoint, then assert.
- Cover the happy path and any explicitly-spec'd error paths. P2 covers the error paths the spec forgot.

If an AC can't be expressed as something observable in the response or downstream state, push back, "system is robust" is not a smoke-testable criterion.

---

## P2: Contract conformance

The shape of every response is locked down to the schema:

- Status code matches the contract.
- `Content-Type` matches (`application/json`, `application/problem+json`, etc.).
- Required fields present; optional fields either present-and-typed or absent (not `null` unless `null` is the spec'd value).
- Unknown fields are not echoed. If the request body has extra fields, the service either rejects them (strict) or strips them (lenient), pick one, don't accidentally do both.
- Pagination shape: `next_cursor` / `total` / `has_more`, whichever the project uses, it appears on every paged response, not just when there are more pages.

If the project has an OpenAPI spec, validate every response against it programmatically, drift between code and spec is the contract violation users hit when their generated client breaks.

---

## P3: Auth matrix

Every protected endpoint gets exercised across an auth matrix. This tier is where the most security defects hide because they don't surface in normal happy-path testing.

| Scenario | Expected |
|---|---|
| No token | 401 |
| Wrong token (malformed / wrong issuer / wrong audience) | 401 |
| Expired token | 401 |
| Valid token, missing required scope | 403 |
| Valid token, valid scope, target resource owned by a different tenant | **404** (not 403, see below) |
| Valid token, valid scope, target resource exists | 2xx |

**The `403 vs 404` tenant-leak.** When the caller is authenticated and authorized for the action class but the specific resource ID belongs to another tenant, return 404, not 403. A 403 leaks the existence of resources outside the caller's tenant. This is routinely missed in code review and routinely flagged in security audits. Bake it into the scenario list.

**JWT-specific:** assert that `alg: none` is rejected and that algorithm-confusion attacks (passing an HMAC-signed token to a service expecting RSA) are rejected. Both have been Auth0 / shared-secret library bugs in the wild within the last five years.

---

## P4: Error shape

Every error response carries a usable payload. The 2026 default is RFC 9457 Problem Details, `application/problem+json` with `type`, `title`, `status`, `detail`, and optionally `instance`. The project may use a different convention; verify it matches what's documented.

Required checks:

- Every 4xx and 5xx response has a body. Empty error bodies are a defect even when the status code is correct.
- No stack traces, SQL fragments, internal hostnames, or library version strings in user-facing errors. Diagnostic detail goes to logs, not the response.
- Validation errors enumerate every invalid field, not just the first one. A form that has to be submitted four times to see four errors is a UX defect.
- Error responses are stable across deploys. Clients pattern-match on `type` (the URI); changing it silently breaks consumers.

---

## P5: Input boundaries

Push every input to its edges. Every endpoint, every parameter:

- `null` where a value is required → 400 or 422, never 500.
- Empty string where a non-empty string is required → 400 or 422.
- Maximum length + 1 → 400 or 422.
- Wrong type (string where number expected, etc.) → 400 or 422.
- Injection-shaped strings (`'; DROP TABLE`, `<script>`, `../../etc/passwd`) → safely rejected or escaped, never crash.
- Unicode edge cases (combining characters, RTL marks, zero-width spaces) → handled without truncation or panic.

A 500 on any of these is a defect. The bar is "the service stays up, returns a typed error, and logs the offending input."

---

## P6: Idempotency

If the endpoint accepts an `Idempotency-Key` header (and modern POST/PUT endpoints should):

- Same key + same body → identical response, no duplicate side effect.
- Same key + different body → 422 (the spec says "do not process a different request under the same key").
- Concurrent dupes with the same key → serialized; only one succeeds, the others return the cached response.
- Keys expire on a documented TTL, typically 24h. Test the boundary.

For non-idempotent endpoints, the loop still verifies that retries are *safe*, a network failure mid-request followed by a retry shouldn't create two of the thing.

---

## P7: Observability (the part teams skip)

Modern smoke tests assert the observability output, not just the API output. The 2026 framing is **Observability-Driven Testing (ODT)**: verify that the running service tells you what it did.

For every scenario:

- A log line was emitted with a trace ID (for cross-domain correlation).
- A span was created for the request, with attributes matching the operation (`http.route`, `db.statement`, downstream call names, match what the project's existing spans look like).
- The relevant counter incremented (request count, error count if applicable).
- The relevant histogram recorded a value (request duration).
- No PII in any of the above.
- 4xx responses are not logged at `ERROR` severity. They're expected user errors; only 5xx and timeouts merit `ERROR`.

A feature that "works" but emits no observable signal will be impossible to debug in production. Treat missing observability as a defect, not a "we'll add it later."

---

## P8: Pagination, rate-limit, and concurrency edges

These are the edges that don't show up in happy-path testing but break under real load:

- **Pagination boundaries**: page 1 with exactly N items (the page size), page 2 with zero items, requesting a page beyond the end → expected behaviour (empty page, not 500).
- **Rate-limit responses**: hitting the limit returns 429 with `Retry-After` and the right `X-RateLimit-*` headers. Continuing to hammer doesn't 500.
- **Optimistic locking**: simultaneous updates to the same resource → one wins, the other returns 409 with the current `ETag` / version. No silent overwrites.
- **Connection pool**: a burst of N+1 requests where N is the pool size doesn't cause cascading timeouts. The (N+1)th queues briefly, doesn't fail.

---

## P9: Latency sniff (don't gate, but observe)

Single-request p95 against a known dataset. This is a sanity check, not a load test.

- The new endpoint's p95 is within an order of magnitude of similar endpoints in the same service.
- A cheap query plan check: hitting the endpoint hits the DB N times, not N² (no N+1 in the new ORM usage).
- No new connection-pool burst that wasn't there before (a single request shouldn't open more than one new connection unless it explicitly fanned out).

Don't gate the PR on this, flaky timing tests cause more grief than they catch. Treat it as a signal: a 10x regression is worth investigating, a 20% regression isn't.

---

## Capturing the test

Once every scenario is green, capture the trajectory as a permanent test in the project's existing framework. Same rules as the UI side:

1. Save to the project's existing test directory (`tests/smoke/`, `e2e/`, `integration/`, or wherever the repo puts integration tests).
2. Name the file for the feature, not the ticket.
3. Match the project's test style, don't introduce a different assertion library or test runner for one new file.
4. Include P1, P2, P3, P4, P6, and P7 scenarios at minimum. P5 input-boundary checks belong here too unless the project has property-based testing that covers them better.
5. P8 edges belong in a separate slower job (load test or nightly integration suite), they're too expensive to run on every PR.

The test file is the artefact that justifies the smoke pass. It catches the next regression before the next person re-discovers the bug in production.

---

## Common gotchas

These are the things teams routinely miss in backend smoke tests. Bake them into the scenario derivation:

1. **403 vs 404 tenant leak**: covered above; the most reliably-missed defect.
2. **Idempotency key not actually de-duping**: the cache write happens but the read doesn't, so the second request still processes.
3. **Timezone bugs in date-bounded queries**: "events on 2026-05-23" returns the wrong rows when the server is UTC and the user is UTC-3.
4. **Off-by-one in pagination**: `LIMIT N OFFSET (page - 1) * N` is correct, `LIMIT N OFFSET page * N` skips the first page silently.
5. **Missing `Retry-After`** on 429, the client has no signal for how long to back off.
6. **Silent connection-pool exhaustion**: requests hang instead of failing fast.
7. **N+1 in the new endpoint**: ORM lazy loading inside a loop. Show up at 10 items, time out at 1000.
8. **No span for the downstream call**: production debugging becomes guesswork.
9. **`ERROR` log level for user errors**: pages oncall at 3am for a 404.
10. **PII in logs / spans / error messages**: quiet GDPR liability that doesn't surface until audit.
