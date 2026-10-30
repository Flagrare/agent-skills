---
name: bug-bash
description: "Programmatic bug bashing, ingest a prescribed test plan (Notion, markdown, pasted spec), drive a real running system (browser via Chrome DevTools / Playwright MCP, backend via API tools when relevant), run every prescribed case with evidence, then do exploratory passes (viewports, edge inputs, multi-actor flows, codebase-driven concerns, additional context like meeting transcripts, emails and links checked in the real inbox with a control case, other languages, failures and races) without ever claiming a bug it didn't itself reproduce. Fills free-text fields with tagged, playful test data that also probes something (unicode, HTML, template syntax, length). Lands results in a local MD file by default, optionally writes back to the source (Notion bug DB, test case Eng QA columns, etc.) in the user's voice. Use whenever the user says 'bug bash', 'QA this feature', 'run the test cases', 'go through this test plan', 'verify these scenarios', 'do a bash on X', when they hand over a Notion test case page, or any time programmatic end-to-end verification of a feature against a checklist is needed. Also use it when a smoke test passed but the user wants more cases tested, or asks 'what else should we test' and then 'test it yourself'. Make sure to use this skill even when the user just says 'test this Notion page' or 'check these scenarios', anything that smells like running someone else's prescribed test plan against a live system."
---

# Bug Bash

A disciplined pass through a prescribed test plan against a real running system. The pass ends when every in-scope scenario has been run, every bug has been *reproduced* (not assumed), evidence is captured, and the results have landed where the user wants them.

This skill exists because of a specific failure mode: when someone hands you a test plan and a transcript of past discussion, the temptation is to just write up "the team already found these bugs" without actually testing. That produces noise, not signal. The whole point of a bash is that *you ran it and saw it*.

---

## Why this exists

Most "QA passes" rot in two directions. Either they're a single happy-path click-through that never finds the interesting bugs, or they're an essay summarizing what other people said in meetings. The first misses real defects; the second pollutes the bug tracker with unverified claims that someone else later has to chase down.

A good bash does the prescribed work *and* explores around it *and* keeps a strict line between "I reproduced this" and "someone mentioned this." That line is what makes the output trustworthy.

The second reason this skill exists: the source-of-truth (a Notion test case database, a PRD with acceptance criteria, a markdown checklist) is usually the most important artifact, and it's the part that doesn't get updated. Filling Eng QA columns, adding bugs to the right database, and posting notes in the team's tone is half the work.

---

## Step 1: Lock the goal explicitly

**Hard requirement.** Before any other tool call, you (the executing model) MUST call `/goal` yourself, not merely state a goal in prose. A bash walks many cases across many turns and emits a large findings file partway through; without a durable goal, the model tends to stop after the strict pass or after writing the findings file, before the exploratory pass and the write-back. `/goal` is a session-scoped Stop-hook: a fast evaluator checks your condition against the conversation after every turn and makes you continue until it holds. (Grounded in [`docs/research/2026-06-11-claude-code-goal-anti-stall.md`](../../../../docs/research/2026-06-11-claude-code-goal-anti-stall.md).)

Surface the goal to the user first so they can correct scope, then call `/goal` with a condition phrased as something your own output demonstrates (the evaluator cannot run tools or read files):

> Bash `[feature / ticket / PR]`: every prescribed test case has been run against the live system with captured evidence and a recorded status (pass / fail / skip-blocked / skip-external); the eight-lens exploratory pass is complete; every bug recorded is one I reproduced myself (no second-hand claims); results have landed in `[user's chosen sink]`; and the close has been confirmed via the Step 8 AskUserQuestion. Stop after 30 turns if not met.

After setting the goal, create a Todo list (TodoWrite), one item per prescribed test case plus one per exploratory lens, so coverage is tracked while the goal keeps the harness from letting you stop early.

**If `/goal` is unavailable** (untrusted workspace, or `disableAllHooks` / `allowManagedHooksOnly` set): proceed without it, but treat each step's completion as mandatory and do not yield the turn until Step 8.

---

## Step 2: Ingest the test plan

Ask the user where the test cases live. The skill must not assume a format. Use `AskUserQuestion` with:

- **Notion URL**: fetch via the Notion MCP, parse the test case database / inline tables
- **Markdown / file path**: read the file, parse the checklist
- **PR / spec description**: paste the URL or text, parse the acceptance criteria
- **Pasting now**: user drops the scenarios directly into chat

After ingestion, restate the test cases back to the user as a numbered list with the *What* and *Should* for each. This is the chance to catch a misread before driving the browser.

If the source contains pre-set columns for results (a Notion "Eng QA" column, a "Status" cell, a checkbox), note them, those are where results will land in Step 7.

---

## Step 3: Detect the target environment

Inspect what's being tested and pick the surface area:

| Signal | Target |
|---|---|
| Test cases describe browser navigation, clicks, form submission, URL changes | `ui` |
| Test cases describe API endpoints, request/response shapes, status codes | `backend` |
| Both | `both` |
| Ambiguous | ask via `AskUserQuestion` |

Verify the right MCP / tool is reachable:

- **UI**: Chrome DevTools MCP or Playwright MCP.
- **Backend**: Postman CLI (`postman:send-request`), `curl` via Bash, or an MCP that hits the service. Confirm before assuming.

If the UI bash needs a browser MCP and neither Chrome DevTools nor Playwright is connected, ask via `AskUserQuestion`:

- **Install or connect a browser MCP (Recommended)**: Chrome DevTools or Playwright. We can pause here while you set it up.
- **You drive the browser, I narrate the cases**: works fine, slower, no automated screenshot evidence.

Read the matching reference for tactics:

- `references/ui.md`, browser-driven flows, isolated contexts, screenshot evidence, viewport handling
- `references/backend.md`, request shaping, auth, status/contract assertions, observability checks
- Read both for full-stack features.

---

## Step 4: Prepare the environment

Three things to confirm before any scenario runs:

1. **Where is the live system?** The user almost always knows from context. If the answer isn't obvious, ask via `AskUserQuestion`:

   - **Production**: the live customer-facing environment.
   - **Staging**: the team's pre-production environment.
   - **Preview deploy**: a PR-scoped deploy. Ask for the URL after picking this.
   - **Localhost**: running on the user's machine. Ask for the port if not given.
2. **Auth.** Default to asking the user to log in themselves in the browser window the MCP is attached to. Automated login is a tarpit, MFA, captchas, OAuth redirects, and corporate SSO all break it. Wait for the user to confirm they're logged in.
3. **Feature flags / preconditions.** If the spec calls out a flag (`release-foo` is on, partner X has `enabled = true`), verify it's set before bashing. If a precondition can only be set by a developer (DB seed, environment toggle), name it and ask them to do it before continuing, don't run a session that's blocked from the start.
4. **Enough data to spend.** Many cases consume a record for good: you can only report an order once, accept an invite once, cancel a booking once. Before the strict pass, ask the app's own list API (from the logged-in page, see `references/backend.md`) for every eligible record, and keep the ids in `localStorage` so a page reload doesn't lose them. Prefer records owned by throwaway or test accounts. If other people are bashing the same environment at the same time (look for fresh records by other users), leave their records alone. When the pool is empty, create fresh records yourself in the test environment rather than stopping to ask.

If the test plan requires multiple user roles (inviter / invitee / admin), use isolated browser contexts (`new_page` with `isolatedContext`), they share no cookies, no storage. This is the only reliable way to test impersonation, invite-acceptance, or cross-tenant flows without log-out/log-in churn.

### Test data with personality

Every free-text field you fill is a chance to test something and to make the results fun to read. Bug bashes are long and the people reading the results are tired; "test test asdf" teaches nothing and nobody remembers it. Write each value as a tiny, plausible scene from the product's world, with a tag up front so it's findable later:

- `MARKETING-OFF #1: Member insisted the oat milk was "spiritually dairy" and demanded a refund in exposure. Told the cashier she would leave a 1-star review on her Spotify.`
- `Race x10: tried to redeem one order for the whole pickleball team.`
- `Double-click test: member returned the same iced latte three times because it was 'too iced', then filmed the barista for TikTok.`

The rules that keep it light without making it noise:

1. **Tag first.** Start with the case it belongs to (`HTML-EMAIL`, `LONG-50K`, `Race x10`), so you can search for it in the inbox, the admin page and the database, and so nobody mistakes it for a real report.
2. **Each value tests something.** The joke is the wrapper; the payload is the point. Fold the probe into the story: accents and emoji (`pediu açaí sem açúcar 😡`), Japanese and Arabic, a `<b>` tag and a link, template syntax (`{{user_first_name}} {% if true %}RAN{% endif %}`), blank lines and bullets, a 50,000-character monologue.
3. **Absurd, never mean.** Invent the people or use the test accounts' own names. No real customers, no colleagues as the villain, nothing about protected traits, nothing you'd mind a stranger reading in a support queue.
4. **Different every time.** A repeated string can't tell you which run produced which row, email or log line.

---

## Step 5: Strict pass: run the prescribed cases

Walk the list in order. For each case:

1. Execute the steps in the live system.
2. Compare actual vs the *Should* clause.
3. Capture evidence: a screenshot for UI, a request/response body for backend, a DOM snapshot when relevant. Save under `[workspace]/bug-bash-screenshots/` with descriptive names (`tc2-03-invite-link-generated.png`, not `screenshot1.png`).
4. Record one of: `pass`, `fail`, `skip-blocked`, `skip-external`.

`skip-blocked` means a prior case failure makes this one unreachable, fix the prior first or surface it.

`skip-external` is for cases that *can't* be run from this seat: expired states needing a DB write, mobile-only flows needing a real device, partner config needing a config push. Name what's missing and who would need to do it. **Do not mark these as pass**: they are not verified.

When a case fails, capture evidence and keep going. Don't fix-as-you-go, a bash is observation, not implementation. The exception is `P0`-equivalent "feature didn't load at all", that blocks everything else. Surface it via `AskUserQuestion`:

- **Stop and triage (Recommended)**: the bash can't produce meaningful results until the page even loads.
- **Continue with the rest**: note the blocker, work around it where possible, return to the blocked cases after the underlying issue is fixed.

---

## Step 6: Exploratory pass

Strict cases catch what the team thought to ask about. Exploratory catches what they didn't. Do this every time the strict pass is done, not "if time allows."

Eight lenses, in this order. See `references/exploratory.md` for tactics on each.

1. **Viewport / responsive**: wide (1920+, 2560+), narrow (375 mobile), default. Headers / counters / lists / modals at each. Almost every visible product has a misaligned header somewhere over 1440px.
2. **Edge inputs and limits**: empty submit, max-length, the boundary case the spec implied but didn't write down (the 3rd invite when the limit is 3, etc.).
3. **Multi-actor flows in isolated contexts**: accept a link as a different identity than the inviter intended; observe what the original actor sees afterward.
4. **Codebase-driven concerns**: read the relevant code paths (model definitions, controllers, validations). Surface untested assumptions: does the invite capture an email? Is there server-side validation matching the client schema? What happens if the token is reused?
5. **Extra context the user provides**: meeting transcripts, follow-up Slack threads, "oh and also test X". **Test it. Don't paraphrase it.** Translating a meeting bullet into a bug entry without reproducing it is the most common failure mode of this skill and the reason for the goal-statement clause about second-hand claims.
6. **Everything the feature sends or links to**: confirmation emails, notifications, help articles, "learn more" links. Read the email in the real inbox, not the "202 Accepted" in the logs. Flip the recipient's settings that could suppress it (marketing opt-out, notification toggles, language), and after every negative result run a control with the setting restored, so you know the setting is the cause. Open every help link and check it describes this feature and the current rules.
7. **Language and locale**: switch the account to another language and walk the flow, including the email. Look for untranslated strings, a subject left in English, and wording that differs between the UI and the email.
8. **Failure and races**: make the submit request fail once (offline) and check the form keeps what was typed; submit the same thing from a second tab after the first succeeded; fire N identical requests at once and count the rows; click Submit twice fast. Check what the user is told each time, not just what the server did.

For each exploratory finding, the rules are the same: reproduce it yourself, capture evidence, record it. If you can't reproduce a finding someone else mentioned, that is itself a useful result, file it as "could not reproduce" with the steps you tried.

---

## Step 7: Land the results

Default sink is a local MD file at the user's working dir: `bug-bash-[feature]-results.md`. Always produce this, it's the audit trail the user reads first.

The MD has these sections:

```
# [Feature] bug bash: [date]

## Summary
| # | Test case | Status | Notes |

## Detailed results
[per test case: step / expected / actual / status / evidence ref]

## Bugs reproduced
[per bug: description / repro steps / evidence (record ids, timestamps) / severity / likely owner / source: strict or exploratory]

## Product calls
[working as built, but someone has to decide: e.g. cancelled orders can be reported, the window counts from placement not pickup]

## Could not verify
[external-blocked items with what's needed and who from]

## Data left behind
[records created, settings changed and whether they were restored]
```

Keep "bug" for behaviour that is wrong by any reading. Behaviour that matches the code but might not match intent goes under product calls, so nobody files a ticket against a decision.

Then ask the user via `AskUserQuestion` whether to also write back to the source:

- **Yes, update source-of-truth (Recommended when source has dedicated fields)**: fill Eng QA columns, add bug entries to the linked bug database, post UX notes in the existing notes section, etc.
- **Local file only**: user will transfer manually later
- **Selective**: show me what you'd write, I'll pick

When writing back, match the team's tone in that source. If the existing Eng QA cells use "✅ CB" style, match. If the bug DB entries are casual / first-person, match. Read the surrounding rows before composing yours. This is what makes the output feel like it belongs there.

If the user authored prior content in a recognizable voice (you can usually tell from earlier rows / comments), mirror it. Conversational, informal, no corporate softening unless that's what the team uses.

---

## Step 8: Confirm goal met

Surface the final state via `AskUserQuestion`:

- **Goal met, wrap up (Recommended)**: every prescribed case has a verified status, exploratory pass complete, all bugs reproduced, sink updated. Move to whatever comes next.
- **Goal met, but more to chase**: user wants to add scenarios or test on another device/browser. Loop back to Step 5 with the new scope.
- **Adjust scope**: external blockers are too many; revise the goal with the user.

The button-prompt is the audit trail. Don't declare done in prose.

---

## Anti-patterns

- **Don't claim bugs you didn't reproduce.** A meeting bullet or a Slack message is not evidence. If you write "BUG-N: X is broken" in the results, you ran the steps yourself and saw it. This is the line that makes the output trustworthy.
- **Don't skip the strict pass to chase a hot tip.** Exploratory comes after, not before. Strict is where the contract with the spec is verified; exploratory is where you go beyond it. Inverting this order produces noise instead of coverage.
- **Don't pass-by-default.** A scenario that can't be run is `skip-external`, not `pass`. Naming what's missing is more useful than pretending it worked.
- **Don't write back to source without permission.** Always ask in Step 7. Notion writes are visible to the team; getting that step wrong creates work for others.
- **Don't automate auth.** Default to manual login. The seven minutes you save on automated login costs you forty when the captcha changes or MFA gates the partner account.
- **Don't paraphrase past discussion into bugs.** Transcripts, PR comments, Slack quotes: each one is a *test target*, not a result. Re-test, then file based on what you saw, not what they said.
- **Don't run with a half-set environment.** Feature flags off, partner missing config, wrong account tier, bash with the right preconditions or stop and get them set. A bash against a broken environment teaches nothing.
- **Don't read state off a label.** A toggle labelled "Opt-in" can be on or off; check the control's actual value (`input.checked`) before you name the condition a case ran under. A case run under the wrong condition proves nothing, and the label is easy to misread.
- **Don't stop at "the server accepted it".** A 202 from the email service, a 200 from the API, a row in the database: each is one hop. The bug in a bash is often the last hop (the inbox, the rendered email, the help page). Follow the output until a person would see it.
- **Don't leave the environment changed.** Every setting you flip (notification toggles, language, flags) gets restored before you finish, and checked by reading it back. List what you created in "Data left behind".
- **Don't depend on external skills.** flagrare skills are self-contained. Use MCP tools directly (Chrome DevTools, Playwright, Notion, Postman) when present; degrade gracefully by asking the user to do the step manually.

---

## Flow position

```
[acceptance criteria written / feature implemented]
     ↓
/flagrare:bug-bash          (this skill, verify the spec with evidence, find what the spec missed)
     ↓
[bugs filed back to source]
     ↓
[follow-up tickets created for sev-1/sev-2]
     ↓
[smoke-test reruns on each fix; bash rerun before release]
```

The bash is distinct from `/flagrare:smoke-test`. Smoke-test is "the feature I just implemented works end-to-end", narrow, ten-minute budget, one author. Bug-bash is "the team's prescribed test plan plus exploratory coverage", wider, longer budget, often runs against features other people built. Both are evidence-driven; they're not interchangeable.

---

## References

- `references/ui.md`, Chrome DevTools MCP / Playwright tactics: isolated contexts, screenshot conventions, viewport sweeps, evidence directory structure, common assertion patterns
- `references/backend.md`, request shaping, auth matrix, contract assertions, status-code checks, observability lookups
- `references/exploratory.md`, the eight-lens framework expanded: viewport sweep checklist, edge-input patterns, multi-actor scenarios, codebase-derived concerns, ingesting transcripts and follow-up context without falling into the "paraphrase the meeting" trap, emails and links checked with a control case, language switches, failure injection and races
