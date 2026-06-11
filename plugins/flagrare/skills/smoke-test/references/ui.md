# UI smoke test: priorities and tooling

This is what gets driven in the priority loop when the domain is `ui` (or the UI branch of `both`). The main SKILL.md describes the loop; this file describes what each priority tier actually checks and which MCP server to drive it with.

The numbered priority order is the same order the loop runs them in. Don't reorder; the dependencies are real, a broken P0 means everything after it is noise.

---

## Tooling split (the 2026 consensus)

Two MCP servers, two jobs.

**Playwright MCP, drive the application.** It exposes the page as an accessibility tree (semantic, deterministic, convertible to a permanent test). Default to this for every scripted scenario. Use `getByRole` / `getByLabel` / `getByText`, never CSS classes, never XPath. CSS classes are an implementation detail that will rename three sprints from now and break the test for no behavioural reason.

**Chrome DevTools MCP, diagnose failures.** It exposes console messages, network requests, performance traces, Lighthouse audits, memory snapshots. Reach for it *after* a scenario fails, not before. Driving the app through Chrome DevTools MCP works but produces brittle automation that can't be converted to a permanent Playwright spec.

When neither MCP is present, ask the user to run the smoke pass manually and paste back the result. Do not pretend a smoke test happened without a real browser.

---

## P0: Preconditions (fail fast, seconds)

P0 catches "the app is dead before the test even started." If any of these fail, stop the cascade and fix P0 first.

- App boots, the dev server responds, the initial document HTML is 2xx.
- No 4xx or 5xx on the initial page load, every request the page makes during boot resolves.
- No `pageerror` event fires, uncaught exceptions during boot are P0, not P2.
- No `console.error` on load, the same threshold applies before any user interaction.

A P0 failure usually means the feature wasn't deployed, the wrong route was navigated, an import is broken, or an environment variable is missing. Fix at the lowest layer (config, route, import), don't paper over with a try/catch.

---

## P1: Acceptance criteria contract (the headline)

Every acceptance criterion from the brief becomes one scenario. Each scenario is driven through the accessibility tree, never through DOM internals.

- Drive via `getByRole`, `getByLabel`, `getByText`. If the selector can't be expressed semantically, that's a defect, the component is missing a role or label, fix it.
- Assert via Playwright's web-first matchers: `await expect(locator).toBeVisible()`, `toHaveText()`, `toHaveValue()`. They retry their assertion (not their action) inside a single timeout, which is the only retry pattern that doesn't hide flake.
- Cover happy paths first, then specified error paths, then specified empty states.
- Include reload + deep-link: navigating to the URL fresh must produce the same state as arriving there via in-app navigation. Bugs that only show up on reload are session/persistence bugs, and they ship.

If an acceptance criterion can't be expressed as a behaviour observable in the browser, that's a defect in the AC, push back to the user before continuing. "User feels welcomed" is not a smoke-testable criterion.

---

## P2: Cross-cutting quality gates (the part teams skip)

These run against *every state* the P1 scenarios produce, the initial state, every interaction, every error state. P2 is where most "shipped broken" defects live in 2026.

### Console

- Zero `console.error`. Not "expected errors." Not a whitelist. If the app emits an error to the console, the user's debugging tool is now lying to them, and a real bug will be missed when it happens.
- Zero `pageerror`. Same logic, uncaught exceptions are bugs by definition.
- Warnings can be reviewed but not gated by default. Some libraries are noisy; the team can opt in to gating warnings later.

### Network

- Zero unasserted 4xx / 5xx. If a 404 is *expected* (e.g. a feature-detection probe), the scenario must assert that, silent 404s are a footgun.
- Zero `requestfailed` events.
- No in-flight requests when the scenario ends. Pending requests at scenario end mean the cleanup contract is broken.

### Accessibility

- Run `@axe-core/playwright` on every distinct state. Configure for WCAG 2.1 AA.
- `axe` catches about 30-40% of real WCAG violations. The other 60-70% need a keyboard walk, automate it.

### Keyboard walk

- Tab from the page root. Every interactive element receives focus in a sensible order.
- Enter / Space activates the focused control.
- Esc closes modal / dropdown / overlay states.
- A skip-to-content link exists on pages with significant navigation.

### Focus management

- A visible focus ring on every focused control (not `outline: none`).
- In modals: focus moves to the modal on open, traps within it, returns to the opener on close.
- On route change: focus moves to the new content's heading (typically the `<h1>` of the new page), not left on whatever was clicked.

### Mobile + reduced-motion + dark-mode

- Run the P1 scenarios at 375×667 viewport at least once. Mobile breaks differently than desktop.
- Toggle `prefers-reduced-motion: reduce`. Animations should be replaced with instant transitions, not played at full speed.
- Toggle `prefers-color-scheme: dark` if the app supports it. Hard-coded colors that pass contrast on light fail on dark.

---

## P3: Exploratory (where AI shines)

Beyond the acceptance criteria. Enumerate edges the spec didn't cover, then test the most likely failure modes:

- **Long / unicode / RTL inputs** in every text field. Hebrew, Arabic, emoji, combining characters. Layouts that break on RTL also break on long English titles in production.
- **Out-of-order state transitions**: click submit before filling required fields; click cancel mid-submit; rapid double-clicks.
- **Slow network**: throttle to "Slow 4G" via Chrome DevTools MCP. Optimistic UIs that don't account for delay reveal here.
- **Network failure mid-action**: what does the app do when the save request fails after a confirmation toast already showed?
- **Browser back button**: does the app handle it gracefully or does state desync from URL?
- **Tab visibility loss**: minimize the tab during a long operation. Does the in-flight request still complete and update state?

These rarely catch every edge a user will hit. They catch the obvious ones the spec didn't mention.

---

## P4: Nice-to-have (don't gate the PR)

Run if budget allows; don't block the loop on them.

- **Lighthouse perf audit**: Performance ≥ 80, Best Practices ≥ 90 as a rough floor. Treat regressions vs the prior pass as a signal, not a gate.
- **Visual regression**: only if the project already has a tool (Chromatic / Percy / Playwright screenshots committed to the repo). A first-time visual baseline is not a smoke-test concern.
- **Cross-browser matrix**: Firefox + WebKit pass for the headline P1 scenarios. Smoke-test budget rarely allows this; relegate to nightly CI if the project has one.

---

## Capturing the spec

Once every scenario is green, capture the trajectory as a permanent Playwright spec:

1. Save to the project's existing Playwright directory (`e2e/`, `tests/playwright/`, or whatever the repo already uses).
2. Name the file for the feature, not the ticket: `feature-name.spec.ts`, not `INT-42.spec.ts`. Tickets get archived; features stay.
3. Use `getByRole` / `getByLabel` / `getByText` exclusively. No CSS classes. No XPaths.
4. Use `await expect(locator).toBeVisible()`, never `await expect(await locator.isVisible()).toBe(true)`. The former retries inside the assertion timeout; the latter is a single read and will flake.
5. Set `retries: 0` for the smoke project in the Playwright config. Flake is a defect; retries hide it.
6. Include the P1, P2, and most-valuable P3 scenarios. P4 stays as a separate slower job if it stays at all.

The spec is the artefact that justifies the time spent on the smoke pass. Without it, the next person re-drives the browser by hand, and the next bug doesn't get caught until production.

---

## Common gotchas

These are the things teams routinely miss in smoke tests. Bake them into the scenario derivation:

1. **Form submit on Enter**: half the time only the click handler is wired.
2. **Loading state covers the whole page**: blocks the user from doing anything else, including cancelling.
3. **Error toasts auto-dismiss**: the user can't read a multi-sentence error that vanishes in 2 seconds.
4. **Disabled states are gray buttons**: but the click handler is still attached.
5. **Date inputs at midnight UTC**: display says yesterday in the user's timezone.
6. **Empty list looks like a loading state**: same height, same skeleton, no copy.
7. **Modal dismisses on backdrop click but eats keystrokes**: Esc doesn't close it.
8. **Submit button stays enabled after first click**: produces duplicate submissions.
9. **Saved-state indicator never clears**: page shows "Saved" forever after the first save.
10. **Routes work via in-app nav but 404 on reload**: client-side router not handling deep links.
