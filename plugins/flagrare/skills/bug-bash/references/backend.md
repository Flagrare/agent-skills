# Backend bug-bash reference

Tactics for bashing API-shaped features: REST endpoints, GraphQL ops, background jobs. Same evidence-first discipline as the UI side — capture the request, the response, the status, the observability signal.

---

## Tool selection

Choices, roughly in order of preference for a bash session:

- **Postman CLI** via `postman:send-request` — fast for one-off calls, persistent variables, environment switching, request history retained
- **`curl` via Bash** — universal, scriptable, no dependency
- **HTTP MCPs** (if the service has one) — sometimes the cleanest path; check before assuming

Use Postman when you'll hit the same endpoint multiple times across the bash — variables let you reuse auth and base URLs without retyping. Use curl for one-shot calls or when scripting a sequence.

---

## Evidence: capture request + response

Every backend assertion needs both halves of the wire log:

```
Request:
  POST /v1/workspaces/invitations
  Headers: { Authorization: Bearer <redacted>, Content-Type: application/json }
  Body: { "inviteeName": "Test Invitee" }

Response:
  Status: 201
  Headers: { Content-Type: application/json, X-Request-Id: abc123 }
  Body: { "id": "uuid-...", "link": "https://..." }
```

Save these as text blocks under `bug-bash-evidence/` with names matching the test case (`tc2-create-invite-api.txt`). Redact bearer tokens / cookies before saving.

---

## Auth matrix

Most backend bugs hide in the auth dimension. For every endpoint touched by the test plan, run at minimum:

| Identity | Expected |
|---|---|
| No auth at all | `401 Unauthorized` |
| Valid auth, wrong tenant / scope | `403 Forbidden` (not `404`) |
| Valid auth, right scope | success path |
| Expired token | `401` with a clear message (not silent 5xx) |

The 403-vs-404 distinction matters: leaking "this resource exists but you can't see it" via 404 vs 403 is a common tenant-leak bug. Some teams intentionally return 404 to hide existence — confirm which philosophy the codebase uses before flagging it.

---

## Contract assertions

If the spec defines a response shape, assert it strictly:

- Required fields are present
- Types match (`id` is a string, `expiresAt` is ISO-8601, not just "some date")
- Optional fields are either absent or correctly typed (no `null` vs missing inconsistency)
- Error responses follow RFC 9457 (Problem Details) if the project uses it — `type`, `title`, `status`, `detail`

When the response is meant to be consumed by a known client, also verify the client's actual usage matches the contract. A field the server includes but the client never reads is fine; a field the client requires but the server omits is a bug.

---

## Status code edges

The interesting status codes are not 200 / 500. They're:

- **204 No Content** vs **200 with empty body** — both valid; the client matters
- **201 Created** vs **200 OK** for `POST` — the spec usually picks one; mixing them is a contract bug
- **207 Multi-Status** for batch endpoints — partial success is correct; "first failure aborts" is usually wrong
- **409 Conflict** for "you tried to create something that already exists" — testing this requires creating the resource twice
- **422 Unprocessable Entity** vs **400 Bad Request** — pick the team's convention and verify consistency

---

## Idempotency

If the endpoint is supposed to be idempotent (most `PUT`, all `DELETE`, some `POST` with idempotency keys), run it twice with the same payload:

- Second call returns the same status as the first
- Side effects happen at most once (no duplicate rows, no duplicate emails sent)
- The response on the second call references the same resource as the first

If the endpoint is *not* idempotent and the spec implies it should be, that's worth flagging.

---

## Boundary inputs

For every field in the request schema, run at minimum:

- Empty / null / missing
- Minimum length (often 1, sometimes 2 — Zod's `.min()` lives here)
- Maximum length (the field validation, then one over)
- Special characters (unicode, emoji, SQL-injection-shaped strings, XSS-shaped strings)

Server-side validation often differs from client-side validation. The client might enforce 2-60 chars on a name field; the server might silently accept 1 char or 100. The client-side rule is a UX nicety; the server is the contract. Verify both.

---

## Observability check

Backend features almost always have an observability story — Datadog spans, structured logs, metrics. The spec rarely calls these out as explicit acceptance criteria, but they're part of "is this feature actually ready for production?"

For each endpoint touched:

- Hit the endpoint, then look for the trace in Datadog (or whatever the team uses)
- Confirm key spans exist with expected tags (user_id, tenant_id, action_type)
- Confirm error responses produce error spans (not just 200-with-error-body)
- If the action should emit a track event or audit log, confirm that too

A feature that works but is invisible to observability is half-done. Note any gaps in the exploratory pass; they're usually small fixes that the team will appreciate.

---

## Idempotency keys, request IDs, correlation

If the API supports `Idempotency-Key` headers, test:

- Same payload + same key → same response (cached)
- Different payload + same key → 409 or 422 depending on convention
- Same payload + different keys → two separate resources created

If the API uses `X-Request-Id` for correlation, confirm:

- Every response includes one
- Logs and traces both reference the request ID
- If the client sends one, the server respects it (echoes back, doesn't generate a new one)

---

## Background jobs / async work

If the endpoint enqueues work rather than doing it inline:

- The synchronous response should indicate "accepted" (`202`) or include enough info to poll
- The job runs (check the queue, check the worker logs)
- The job is idempotent or has dedupe (otherwise replays cause data corruption)
- Failures are retried with backoff and eventually dead-lettered

You usually can't directly test async work in a single bash session — note what you observed and what you'd need (queue inspection, worker logs) to verify the rest. That's a `skip-external` if the user can't get you there.

---

## Common assertion patterns

| Spec says | How to verify |
|---|---|
| "Endpoint requires auth" | Hit without auth → expect 401 |
| "Endpoint returns the new resource" | Parse response, assert `id` and key fields |
| "Endpoint rejects invalid input" | Send invalid payload → expect 4xx with field-level detail |
| "Endpoint is idempotent" | Run twice; second response matches first; no duplicate side effects |
| "Action emits event X" | Trigger endpoint; check Datadog for span/log matching event name |
| "Action updates record Y" | Trigger endpoint; query record directly; assert state transition |
| "Endpoint paginates" | Request page 1 + page 2; assert no overlap, page count matches total |

---

## When you need DB access

Some assertions are only verifiable by reading the database directly: "the row was marked deleted but not removed", "the foreign key links to the right parent", "the soft-delete tombstone has the right timestamp."

Most teams don't give shared DB access freely. Use what you can:

- A read-only DB MCP / role if it exists
- An admin UI / internal tool that surfaces the record
- Asking a developer with access to verify the specific row state

Don't fake it. "Probably correct" is not verification.

---

## Capturing as a regression test

When the bash is done, the backend equivalent of "capture as a permanent test" is a test file in the project's framework — pytest / vitest / jest / cargo test / go test — matching the surrounding code. Include:

- Schema assertions (response shape)
- Status code assertions
- Auth matrix (at least the 401/403 split)
- Error-shape assertions (the 4xx response format)
- The observability span / log assertion if the framework supports it

This is opt-in per the same logic as the UI side — only do it when the user is ready to land regression coverage.
