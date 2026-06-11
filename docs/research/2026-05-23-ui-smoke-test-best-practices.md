# UI Smoke Test Best Practices: 2026

**Research date:** 2026-05-23
**Researcher:** Claude (Opus 4.7)
**Purpose:** Inform a Claude Code skill that drives a real browser (via
chrome-devtools-mcp or playwright MCP) to smoke-test a UI feature after
implementation and before opening a PR. Catches console errors, network
failures, broken keyboard nav, missing focus, accessibility issues, 
then fixes and re-tests.

---

## 1. Terminology: where this skill sits

Modern (2025-2026) industry definitions, which align across CloudBees,
BrowserStack, Harness, Katalon, and LaunchDarkly:

| Term | Scope | Speed | When |
|---|---|---|---|
| **Smoke** | Broad-but-shallow. "Does the build burn when you turn it on?" Mission-critical heartbeat. | < 10 min | After build, before deeper testing |
| **Sanity** | Narrow-but-deep on one change. "Does this specific change behave?" | Fast, focused | After targeted fix on stable build |
| **Regression** | Full suite. Everything the app does. | Slow | Before release |

**Where the skill sits:** A *hybrid of smoke + sanity*, biased toward
sanity. It's scoped to *one feature*, but exercises every behavior of
that feature (acceptance criteria + exploratory probes + cross-cutting
quality gates like a11y/console/network). It runs after implementation,
before PR. Internally, treat the acceptance-criteria pass as "smoke"
(must pass to continue) and the exploratory + quality-gate pass as
"sanity" (deep on the changed surface).

The "mission-critical heartbeat" framing matters: if the smoke takes
longer than ~10 minutes, devs skip it. Keep it tight; lean on the
parallel agent's ability to fan out across categories.

---

## 2. The Testing-Pyramid-vs-Trophy debate: current state

- **Kent C. Dodds' Testing Trophy** (still the dominant frontend
  framing in 2026): Static → Unit → **Integration (largest)** → E2E.
  Guiding principle: *"The more your tests resemble the way your
  software is used, the more confidence they can give you."*
- **web.dev's 2024+ "Pyramid or Crab" article** ratifies the trophy as
  a modern best practice and warns against chasing coverage %. It
  introduces the *Crab* (UI-heavy + visual, for small projects) and
  *Diamond* (less unit, more integration) as legitimate variants.
- For a *pre-PR browser-driving agent*, the relevant layer is the top
  of the trophy: E2E / UI integration. The skill should not duplicate
  unit-test coverage, it should validate behavior that only a real
  browser can prove.

---

## 3. What a complete smoke-test pass actually covers: priority order

Organized by what to run first. The ordering matters because cheap
checks should fail fast and gate the expensive ones.

### Priority 0: Preconditions (seconds)
1. App boots, no crash on initial render.
2. No 4xx/5xx on the initial document/HTML response.
3. No uncaught JS errors during initial load (`page.on('pageerror')`).
4. No console errors at level `error` during initial load.

### Priority 1: Acceptance criteria (the explicit feature contract)
5. Each behavior listed in the ticket/spec is exercised end-to-end
   through real user-facing interactions (`getByRole`, `getByLabel`,
   `getByText`). Web-first assertions (`await expect(...).toBeVisible()`)
   only, never `isVisible()` polled by hand.
6. Happy paths first, then specified error paths.
7. State persistence: reload, back/forward, deep-link directly to the
   feature URL.

### Priority 2: Cross-cutting quality gates (the "smoke" part most teams skip)
8. **Console**: zero `error` and zero unexpected `warn` across the whole
   flow. Subscribe to `page.on('console')` and `page.on('pageerror')`
   from the first navigation.
9. **Network**: zero 4xx/5xx (except those the feature legitimately
   asserts), zero failed requests, no requests still pending at
   "test complete." Subscribe to `page.on('requestfailed')` and
   `page.on('response')`.
10. **Accessibility (automated baseline)**: `@axe-core/playwright` scan
    on every state/route the feature exposes. Block on
    `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` violations.
    *Known limit: automated tooling catches only 30-40% of real WCAG
    violations* (Deque, accesify.io 2026). Treat axe-clean as necessary,
    not sufficient.
11. **Keyboard navigation**: Tab through every interactive element on
    every state. Verify (a) every interactive is reachable, (b) tab
    order is logical, (c) `Enter`/`Space` activate, (d) `Escape` closes
    overlays/modals.
12. **Focus**: visible focus ring on every focusable element; focus
    trap inside modals; focus returned to opener on close; focus moved
    to new content on route change.
13. **Forms**: required-field validation, error-message association
    via `aria-describedby`, submit-button disabled-while-pending state.

### Priority 3: Exploratory probes (sanity, AI-leverage shines here)
14. Edge inputs: empty, very long, unicode, RTL, copy-pasted with
    formatting, leading/trailing whitespace.
15. State transitions out of order: rapid double-click, navigation
    mid-mutation, browser back during async work.
16. Reduced bandwidth / slow network (Chrome DevTools MCP emulation).
17. Viewport: at least one narrow mobile (375px) and one desktop
    (1280px+) pass.
18. Reduced motion / dark mode / forced-colors media-query toggles if
    the feature has any motion or theming.

### Priority 4: Nice-to-have (overkill for a single feature's smoke,
mention but don't gate)
19. Lighthouse Performance on the changed route (gate at ≥ 0.9 only if
    the feature is perf-sensitive; otherwise informational).
20. Visual regression (Chromatic / Playwright `toHaveScreenshot()`), 
    only meaningful if the project already has baselines.
21. Cross-browser pass, Chromium is enough for pre-PR smoke; full
    matrix belongs in regression.

---

## 4. Console / Network / A11y: the minimal bar in 2026

These are the three gates teams routinely under-instrument. The
industry-current minimums:

- **Console:** zero `error`, zero `pageerror`. `warn` is a project
  decision but should be inventoried, net-new warnings during a
  feature smoke are a smell.
- **Network:** every request the app issues during the flow is either
  ≤ 399, or asserted-failure (e.g., a test of an error state). Zero
  CORS errors. Zero requests still in-flight at test end.
- **Accessibility:** `@axe-core/playwright` with WCAG 2.1 AA ruleset
  on every meaningful state. Color contrast, image alt, link/button
  accessible name, document title, form-label association are
  blockers. Lighthouse a11y score ≥ 0.9 is a coarser secondary gate
  (Lighthouse runs a subset of axe rules, ~50 vs axe's ~96).
- **Manual a11y supplement:** keyboard-only walk-through + screen
  reader spot-check on any custom widget. Automation cannot replace
  this; the skill should *at minimum* simulate the keyboard walk.

---

## 5. AI-assisted UI testing: what emerged in 2024-2026

- **MCP standard (late 2024)** turned LLM-driven browser control into
  a portable pattern. Playwright MCP (Microsoft, 2025) and Chrome
  DevTools MCP (Google, Sep 2025) are the two production-grade
  servers.
- **Playwright MCP sends the accessibility tree, not screenshots or
  raw HTML**, this is the architectural breakthrough. It means the
  LLM reasons about *semantic structure*, which (a) is cheaper, (b)
  is more deterministic, (c) directly converts to a Playwright script
  you can keep as a regression test.
- **Chrome DevTools MCP** is complementary: ~29 tools across nav,
  input, debugging, network, performance trace, Lighthouse. Best for
  *diagnosis*, reading console, inspecting failed network calls,
  profiling, not for driving user workflows. As of Dec 2025 it can
  attach to a live user session via `--autoConnect`.
- **Selection rule** (per Steve Kinney, 2026): **Playwright MCP for
  driving** the smoke flow; **Chrome DevTools MCP for debugging**
  when something fails. A skill that does both can use Playwright MCP
  as the default and reach for Chrome DevTools MCP when it hits a
  failure it needs to diagnose.
- **Autonomous exploratory testing** has become a production pattern,
  not research. Agents act as curiosity-driven probes building a live
  state-machine model of the app, surfacing interaction paths a human
  wouldn't enumerate. Strong fit for the "exploratory" half of this
  skill's mandate.
- **Convert successful agent runs into scripted tests.** The 2026
  consensus is to capture the agent's working trajectory as a
  Playwright spec, so the next run is deterministic.

---

## 6. Common gotchas teams routinely miss

1. **Console errors are noise, not silence.** Teams whitelist them
   away. The skill must default to *zero tolerance* and require an
   explicit allowlist per project.
2. **Network requests that "succeed" with a 200 but return an error
   body.** Status code alone isn't a gate; check for `ok:true`-style
   contracts in API responses where the contract is known.
3. **Smoke that only tests the happy path.** Each acceptance criterion
   usually has at least one specified error case that is just as much
   part of the contract.
4. **Focus management on SPAs.** Route changes don't move focus by
   default, screen-reader users get stripped of context. Every
   in-app navigation should be verified to move focus to the new
   landmark/heading.
5. **Reload and deep-link.** The feature works *after you arrived
   via the in-app path*, but breaks if reloaded or deep-linked.
6. **`isVisible()` polled manually instead of `expect().toBeVisible()`**
leading cause of flake. Always use web-first assertions.
7. **`getByText` on non-interactive strings as a substitute for
   `getByRole`.** Brittle to copy changes; fails the "tests resemble
   how users use the app" principle.
8. **Forgetting that a11y automation catches ~35%.** A green axe
   report does not mean accessible. Pair with the keyboard walk.
9. **Tests that pass once and never again.** Set `retries: 0` for the
   smoke project so flake is loud. Investigate, don't retry.
10. **Smoke tests that grow into full regression.** > 10 min means
    devs skip it. Cap the budget; promote anything heavier to a
    separate regression run.
11. **Not capturing artifacts.** Playwright trace on first retry
    (CI) and always on (local debug), without traces, agent-driven
    failures are uninvestigable.
12. **Login as a step in every test.** Move auth to a fixture / saved
    storage state. Saves orders of magnitude of run time.

---

## Sources

Searches and fetches dated 2026-05-23.

- [Best Practices | Playwright](https://playwright.dev/docs/best-practices)
- [Accessibility testing | Playwright](https://playwright.dev/docs/accessibility-testing)
- [Network | Playwright](https://playwright.dev/docs/network)
- [The Testing Trophy and Testing Classifications, Kent C. Dodds](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- [Write tests. Not too many. Mostly integration., Kent C. Dodds](https://kentcdodds.com/blog/write-tests)
- [Pyramid or Crab? Find a testing strategy that fits, web.dev](https://web.dev/articles/ta-strategies)
- [The Smoke, Sanity, and Regression Testing Triad, CloudBees](https://www.cloudbees.com/blog/the-smoke-sanity-and-regression-testing-triad)
- [Smoke Testing vs Sanity Testing, BrowserStack](https://www.browserstack.com/guide/sanity-testing-vs-smoke-testing)
- [Smoke vs Sanity Testing, Harness](https://www.harness.io/blog/differences-between-smoke-testing-and-sanity-testing)
- [Smoke Testing in Software Development, LaunchDarkly](https://launchdarkly.com/blog/comprehensive-guide-smoke-testing-software-development/)
- [Smoke Test in Software Testing: 2025 Guide, LoadFocus](https://loadfocus.com/blog/2025/10/smoke-test-in-software-testing)
- [15 Best Practices for Playwright Testing in 2026, BrowserStack](https://www.browserstack.com/guide/playwright-best-practices)
- [UI Smoke Tests With Playwright, Lincoln Loop](https://lincolnloop.com/blog/ui-smoke-tests-with-playwright/)
- [Smoke Testing Your SaaS with Playwright, Makerkit](https://makerkit.dev/blog/tutorials/smoke-testing-saas-playwright)
- [How to Detect and Avoid Playwright Flaky Tests in 2026, BrowserStack](https://www.browserstack.com/guide/playwright-flaky-tests)
- [axe DevTools vs Google Lighthouse Accessibility (2026), inclly](https://inclly.com/resources/axe-vs-lighthouse)
- [Playwright Accessibility Testing: What axe and Lighthouse Miss, David Mello](https://www.davidmello.com/software-testing/test-automation/playwright-accessibility-testing-axe-lighthouse-limitations)
- [Accessibility Testing Automation: axe + Pa11y + Lighthouse CI, Accesify](https://www.accesify.io/blog/accessibility-testing-automation-axe-pa11y-lighthouse-ci/)
- [Accessibility Testing in CI/CD: Complete Integration Guide, TestParty](https://testparty.ai/blog/accessibility-testing-cicd)
- [axe-core, Deque](https://www.deque.com/axe/axe-core/)
- [Runtime Tools Compared: Playwright MCP, Chrome DevTools MCP, and Claude in Chrome, Steve Kinney](https://stevekinney.com/courses/self-testing-ai-agents/runtime-tools-compared)
- [Playwright vs. Chrome DevTools MCP: Driving vs. Debugging, Steve Kinney](https://stevekinney.com/writing/driving-vs-debugging-the-browser)
- [Chrome DevTools MCP vs Playwright MCP vs Playwright CLI, Test-Lab.ai](https://www.test-lab.ai/blog/chrome-devtools-mcp-vs-playwright-mcp-cli)
- [6 most popular Playwright MCP servers for AI testing in 2026, Bug0](https://bug0.com/blog/playwright-mcp-servers-ai-testing)
- [Browser Tools for AI Agents Part 1, DEV / Steven Gonsalvez](https://dev.to/stevengonsalvez/browser-tools-for-ai-agents-part-1-playwright-puppeteer-and-why-your-agent-picked-playwright-k71)
- [Autonomous Browser Testing: Playwright and Chrome DevTools MCP, Medium](https://medium.com/@sbasil.ahamed/autonomous-browser-testing-using-playwright-and-chrome-devtools-mcp-11817eb413e5)
- [Autonomous Exploratory Testing: How AI Finds Hidden Bugs, TestQuality](https://testquality.com/autonomous-exploratory-testing-ai-agents/)
- [Frontend Testing Guide, Chromatic](https://www.chromatic.com/frontend-testing-guide)
- [How to create efficient UX smoke tests with synthetic monitoring, Datadog](https://www.datadoghq.com/blog/smoke-testing-synthetic-monitoring/)
