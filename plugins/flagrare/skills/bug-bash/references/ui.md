# UI bug-bash reference

Tactics for bashing browser-driven features via Chrome DevTools MCP (default) or Playwright MCP. The principles transfer; the tool names differ.

---

## Tool selection

If both MCPs are connected, **prefer Chrome DevTools MCP** for bashing because:

- Snapshots return text + UIDs (faster than parsing screenshots)
- Native network request capture without setup
- `isolatedContext` is a first-class concept, multiple identities in one session
- `evaluate_script` is unrestricted, useful for URL checks, Redux store inspection, clipboard reads

Playwright is a better fit when:

- The bash needs to land as a permanent test file at the end (Playwright's codegen is the standard there)
- The team's existing E2E suite is already Playwright, match the surrounding code

Either way, never assume the MCP is connected. Call `list_pages` (Chrome DevTools) or the equivalent first, if it errors, ask the user to connect it before continuing.

---

## Snapshot vs screenshot

Use `take_snapshot` for assertion logic (it has UIDs, it's text-indexable, it's cheap). Use `take_screenshot` for *evidence* (the artifact a human reviews later).

A common pattern:

```
take_snapshot       # to find the uid of the button
click(uid=X)        # interact
wait_for([...])     # ensure the next state rendered
take_snapshot       # to assert the new state
take_screenshot     # to save evidence under bug-bash-screenshots/
```

Snapshots go stale the instant the page changes, always take a fresh one before the next `click` or `fill`.

---

## Isolated contexts

When the test plan involves more than one actor (an inviter sends; an invitee accepts), use `new_page` with `isolatedContext: "<name>"`. Pages in different isolated contexts share nothing, no cookies, no localStorage, no service worker. This is the only safe way to simulate "another user" without logging out and back in across the same browser session.

Naming convention: name the context after the role, not the test step. `inviter`, `invitee`, `admin`, `incognito-shopper`. Future-you will thank present-you.

Close isolated contexts at the end of the bash (`close_page`), they accumulate fast across a long session.

---

## Evidence directory

Save all screenshots and capture artifacts under `bug-bash-screenshots/` (sibling to the results MD) with a naming scheme that lets a human reader sort them:

```
bug-bash-screenshots/
├── 00-logged-in.png
├── tc1-01-settings-share-tab-visible.png
├── tc1-02-share-tab-content.png
├── tc1-03-after-reload-share-persists.png
├── tc2-01-create-invite-modal.png
├── tc2-02-validation-error.png
├── ...
├── bug1-canceled-still-visible.png
├── bug2-expired-no-delete.png
├── exploratory-wide-viewport-2560.png
```

`tc<N>-<step>-<short-desc>` for prescribed cases. `bug<N>-<short-desc>` for reproduced bugs. `exploratory-<theme>-<detail>` for exploratory findings. The order ID (`01`, `02`) matters because filesystem and gallery sort puts them in run order.

---

## Viewport sweep

Default desktop testing happens around 1440×900. Two more sweeps catch most layout bugs:

- **Wide**: 1920×1080 (most monitors) and 2560×1440 (developer monitors). Headers, hero sections, and "centered" content reveal misalignment here. Counters and lists often grow into the wrong column.
- **Narrow**: 375×812 (iPhone size). Modals, dropdown menus, copy buttons, and toasts often spill outside bounds.

Use `resize_page(width, height)` between captures. Take a screenshot at each width, not a snapshot. Visual issues are visual; the a11y tree won't tell you the header is offset by 80px.

This is also where the spec almost never has explicit assertions, it's pure exploratory. Trust your eye; if it looks wrong it usually is.

---

## URL and route assertions

`evaluate_script(() => window.location.href)` is the reliable way to confirm SPA routes. Don't trust the URL bar in a screenshot, it can lag a frame behind the actual route change.

For SPA tab states (`?tab=share`, `#section`, etc.):

- Query params survive reload + reload-renders-the-right-tab is a common acceptance criterion. Always test reload after any route change.
- Hash fragments don't appear in server logs. If the spec uses a hash, note it as a debugging/observability tradeoff in the exploratory results.

---

## Network request evidence

For acceptance criteria like "the API gets called with the right payload":

```
list_network_requests({resourceTypes: ["fetch", "xhr"]})
get_network_request(reqid)
```

Filter to the request of interest, confirm status, peek at response body. Save the body to evidence if the assertion is content-shape (e.g., "response contains `id` and `link`").

---

## Common assertion patterns

| Assertion in spec | How to verify |
|---|---|
| "Element is visible" | snapshot contains the element with no `hidden` / `disableable disabled` attributes |
| "Button is grayed out" | snapshot shows `disableable disabled` on the button; click attempt fails with timeout |
| "URL changes to X" | `evaluate_script(() => window.location.href)` returns expected URL |
| "Toast appears" | `wait_for([toast text])` + snapshot shows the toast region |
| "Modal closes" | snapshot no longer contains the `dialog` role |
| "Data persists after reload" | `navigate_page(type: "reload")` then snapshot the expected state |
| "Counter updates from N to N+1" | snapshot the counter text before and after the action |
| "Clipboard contains X" | `evaluate_script(() => navigator.clipboard.readText())` (may need permissions; the toast confirming copy is usually enough) |

---

## Forms and validation

For form-based test cases, always test the validation cases *before* the happy path. Submitting an empty form usually exercises the most fragile code (Zod schemas, async validators, race conditions between client and server validation). If validation errors render, the happy path is more likely to work.

Order:

1. Submit empty, expect required-field error(s)
2. Submit with one field, expect remaining errors
3. Submit with invalid value (too long, wrong format), expect field-specific error
4. Submit valid, expect success state

For each, snapshot the error region by name (`alert` role, `FieldError` text).

---

## Reload and persistence

A surprising number of bugs hide in "what happens when the user reloads?" State that lives in URL params, query strings, or localStorage should survive a reload. State that lives only in component memory (`useState` not connected to a router or store) won't. The spec often calls this out as an explicit assertion ("reload renders the right tab"), always run it.

Pattern:

```
navigate_page(type: "reload")
wait_for([expected-text])
take_snapshot       # confirm same state
take_screenshot     # evidence: post-reload
```

---

## When the MCP is fighting you

Common failure modes and fixes:

- **`click` timeout**: the element is in the snapshot but not interactive (often a backdrop or transition state). Take a fresh snapshot; UIDs change. If the new snapshot still has the same UID and click still times out, check if a modal is intercepting the click.
- **`navigate_page` timeout but page actually loaded**: Chrome DevTools sometimes signals timeout while the page is still rendering rich frames (Vimeo embeds, third-party widgets). Check `list_pages` for the actual URL; if it's the expected one, proceed.
- **Stale snapshots**: never reuse a UID across an action that changes the DOM. The text-based outputs are cheap; take a new snapshot every time.

---

## Capturing the trajectory as a permanent test

When the bash is done and the user wants the regression captured, generate a Playwright spec via the MCP's codegen. One file per feature, named `<feature>.spec.ts`. Use `getByRole`, `getByLabel`, or `getByText` selectors, never CSS classes. Keep the same scenario order and priorities; the spec becomes the next person's bash baseline.

This is optional and user-driven. Don't write a spec by default, it's a separate step that should only happen when the user is ready to land regression coverage.
