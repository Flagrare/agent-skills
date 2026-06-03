# Exploratory pass reference

The five lenses, expanded. The strict pass covers the spec; the exploratory pass covers what the spec didn't think to ask for. Run all five — they catch different classes of bug.

The rule that runs through every lens: **you can only file what you reproduced.** Hypotheses are not bugs. Things people mentioned are not bugs. Things the codebase suggests might be wrong are not bugs. They are *test targets* — you turn them into bugs by reproducing them.

---

## Lens 1 — Viewport / responsive

Most features are designed at one viewport (laptop, ~1440px) and ship without anyone looking at them elsewhere. The exploratory sweep catches this in five minutes.

Checklist per viewport:

- Page header alignment (center vs left vs flush)
- Cards / lists wrap correctly, no overflow
- Modals fit the viewport — not taller, not wider, no scroll required for content
- Dropdowns position correctly relative to their trigger (no clipping off-screen)
- Toasts / notifications appear in the right corner, don't overlap buttons
- Forms don't break (inputs not crammed, labels visible)
- Touch targets are reachable on narrow widths

Run at: 375 (mobile), 1024 (tablet), 1440 (default desktop), 1920 (FHD), 2560 (QHD).

The most common bug at 1920+ is a header that's left-aligned to the content container while everything else is centered to a max-width. Look for this specifically.

The most common bug at 375 is modals overflowing or buttons getting too close together to tap.

---

## Lens 2 — Edge inputs and limits

For every input field and every limit the feature has:

- Empty / null / whitespace-only submission
- Min boundary (limit - 1, limit, limit + 1)
- Max boundary (same shape)
- Wrong type (number where text expected, etc.)
- Special characters: unicode, emoji, RTL text, SQL-shaped strings, XSS-shaped strings, very long strings
- Duplicate / repeat submissions (especially clicking the submit button twice fast)

For limits:

- Hit the limit exactly — does the action succeed and the limit decrement?
- One past the limit — does the right error fire?
- After hitting the limit, does the UI reflect it (button disabled, banner shown)?
- After freeing up capacity (cancel one of N=3, now N-1), does the limit refresh?

A practical example: a "3 invites max" feature has at least six interesting states: 0/3, 1/3, 2/3, 3/3, "tried-to-create-4th", and "canceled-one-from-3-back-to-2." The spec usually asserts 3/3-disabled; the exploratory pass catches that the 2-after-cancel state correctly re-enables.

---

## Lens 3 — Multi-actor flows

Anything that involves more than one user role needs to be tested across roles in isolated browser contexts. Examples:

- Invite flows: create as A, accept as B, observe as A
- Sharing: share from A, view from B, revoke from A, observe from B
- Admin actions: change state in admin panel as admin, observe in user app as the affected user
- Tenant boundaries: do something as tenant 1, confirm tenant 2 cannot see it

Setup: `new_page` with `isolatedContext: "<role-name>"` for each actor. Pages in different isolated contexts share zero state. Switch between them via `select_page(pageId)`.

Common bugs this surfaces:

- The other actor's view didn't update after an action (stale React Query cache, missing websocket invalidation)
- A field that's set by actor A gets silently overwritten by actor B's account creation (for example: the inviter's chosen name for the invitee gets replaced by whatever name the invitee sets for themselves when they accept)
- Authorization gaps — actor B can see something they shouldn't because the API filter is client-side, not server-side

---

## Lens 4 — Codebase-driven concerns

Read the feature's code paths. The exploratory pass benefits hugely from a 5-minute read of:

- The model / migration that defines the feature's data shape
- The route / controller that handles requests
- The service layer that does the work
- The validation schema (Zod, Joi, equivalents)

What to look for:

- **Fields that aren't captured but feel like they should be** — invite has a name but no email? That's testable: anyone with the token link can accept as anyone.
- **Validation gaps between client and server** — client trims and `min(2)`; server accepts 0-char names? Verify.
- **Tokens / secrets / IDs in URLs or response bodies** — is the token in the URL? It will end up in server logs, browser history, referrer headers. Worth noting.
- **Implicit assumptions** — "the invite has been used" is checked by `acceptedByUserId IS NOT NULL`, but the token itself isn't invalidated on use? That's a subtle replay risk.
- **Soft-delete tombstones still visible to the user** — does the UI show records that the API says are deleted?

When you find a concern, treat it as a test target. Construct a scenario that proves it. If you can reproduce it, file it. If you can't reproduce it but it looks risky on read, file it as a "code observation, not reproduced" — distinct from "bug." That distinction is what keeps the bug list signal-rich.

---

## Lens 5 — Extra context the user provides

This is where the most common failure mode lives. The user pastes a meeting transcript, a Slack thread, a follow-up email. There are bullets like "the URL looks like an API endpoint" and "the name silently changes." It's tempting to take each bullet and file it as a bug.

**Don't.** Each bullet is a test target. Run the scenario yourself. If you reproduce it, file it with evidence. If you can't reproduce it, surface that — "tried X, saw Y, did not reproduce the reported behavior" is useful data.

The reasoning: meeting bullets are summaries, often imprecise. A team member may have seen the bug under specific conditions you don't know about (different account, different feature flag, different timezone). Filing a bug based on a half-remembered phrasing means a developer will later be unable to reproduce it and will close it as "cannot reproduce" — but now everyone's energy is spent.

Instead:

1. Read the extra context.
2. For each claim, plan how to reproduce it.
3. Run the scenario.
4. File based on what you saw — with the original context as supporting material, not as the bug description itself.

Practical example from a workspace-invites bash:

- Transcript claim: "the URL looks like an API endpoint."
- Test target: capture the invite URL when generated; inspect format.
- Reproduced: URL is `api-staging.example.com/v1/users/workspaces/invitations/accept?token=...`
- File as: "Invite URL exposes API path; production will be `api.example.com/...` — verified by inspecting generated URL in [screenshot]." Cite the transcript as the surfacing source.

The bug entry says "I saw this," not "they said this." Same conclusion, more useful provenance.

---

## When a lens turns up nothing

It's fine. Note that the exploratory pass for that lens found no issues. "No findings" is itself a useful data point — the next person doing a bash will know that area was already scrutinized.

What's *not* fine: skipping a lens to save time. The reason to do all five is that each catches a different class of bug. Skipping the codebase lens is what lets the "anyone with the link can accept" issues ship. Skipping the viewport lens is what lets the header-misalignment issues ship. Each one is twenty minutes, max, and finds the bugs that nobody else will.

---

## Severity for exploratory findings

Use the same scale the project uses for prescribed bugs (P0/P1/P2/P3 is common). Be honest:

- **P0** — feature is broken; production would fall over
- **P1** — significant user-visible bug or security concern; must fix before release
- **P2** — bug or UX issue with workaround; should fix soon
- **P3** — polish, edge case, low-frequency

Exploratory findings often skew toward P2/P3 because the prescribed cases caught the P0/P1s already. That's expected. But occasionally exploratory turns up a P0 — like "the invite acceptance flow skips the entire MFA setup" — and when it does, surface it immediately rather than burying it in the results doc.
