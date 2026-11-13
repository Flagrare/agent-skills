---
name: support-triage
description: Investigate a support, ops, onboarding or account-manager report about a customer, venue, account or order end to end, then draft a threaded chat reply in the user's voice. Use whenever someone reports a production problem in a channel ("items disappeared", "can't find these to price", "no orders since last week", "the dashboard says Available but customers can't buy it", "stuck in Pending review", "the conversion didn't take"), or the user says "take a look at this message", "investigate this", "check everything you can", "what's going on with this account/venue", "help support with this", or pastes a chat link to a support thread. Also use when a teammate tags the user on a customer question, even if they don't ask for an investigation.
---

# Support triage

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. See `/flagrare:write-docs`.

Support reports look different every time, but the investigation is the same loop: find the entity, place it in the right state, read what the data, logs and code actually say, check every claim, then answer in the thread. Most wrong answers come from skipping a step: answering from memory, trusting a field that means nothing, or replying at the root of a channel instead of in the thread.

The output is a **chat draft** in the reporter's thread plus a short summary for the user. This skill never posts; the user sends.

## Setup: the company profile

Everything company-specific lives outside the plugin, so it survives updates and stays private:

- `~/.claude/skills/flagrare/support-triage/profile.md`: how this company's support questions work.
- `~/.claude/skills/flagrare/support-triage/recipes.md`: the exact queries and commands for each data source.

Read both at the start of every run. If they don't exist, build them before investigating, in this order:

1. **Harvest what's already known.** Read `~/.claude/skills/flagrare/config.json` (chat handle, repos, ticket tracker), the career `voice.md` if present, the project's `CLAUDE.md`, and any saved memories about data access, logs or the product's domain. Look at connected MCPs and CLIs (warehouse, logs, chat, tracker, browser).
2. **Ask only for the gaps**, one short question at a time, with a sensible default offered:
   - What is the main entity support asks about (venue, account, store, workspace), and what id identifies it?
   - What states can it be in that change what its customers see (plans, integration types, migration phases)?
   - Where does the data live (warehouse and connection, key tables), and how should it be read (a delegated agent, a CLI, a BI tool)?
   - Where do application logs live (and which tool is *not* the right one, if a team often guesses wrong)?
   - Which repos hold the customer-facing view, the internal admin view and the backend?
   - Is there a public page per entity, and what's its URL pattern?
   - Where are replies drafted, and is anything ever posted directly? (Default: drafts only, always in the thread.)
3. **Write the profile** with these sections: Entity and states, Data sources, Logs, Code map, Public view, Reply rules, Known traps (empty at first). Put query text in `recipes.md`, not in the profile.
4. Tell the user in two lines what you saved and where, then continue with the investigation.

Each later run adds to the profile: a trap that cost time goes into **Known traps** with one line on how it misled you; a query you had to work out goes into `recipes.md`.

## 1. Read the report and everything around it

- Read the whole thread through the profile's chat reader, including replies that came in while you worked. If someone is already on it, say who and what's left. A question asked by someone else does not mean it's handled; the user decides whether it's theirs.
- Note who reported it and their role. Ops, finance, sales and account managers need different words. Check the role instead of guessing it.
- Collect the entity id, linked cases or tickets, screenshots (describe them) and dates.
- Search chat and meeting notes for the same entity or symptom in recent weeks. Earlier threads often hold the first half of the story: an earlier outage, a previous migration, a product decision already made.

## 2. Place the entity

Look up the entity's state using the profile's recipe. Use the state silently: the user knows the domain, so name what's unusual, not the basics. Compare with a healthy sibling (same chain, plan or integration) when something looks off; one that works today is the fastest proof of what "normal" looks like.

## 3. Gather evidence

Run independent lookups in parallel. For each, ask the question the report raises:

- **What can customers actually do right now?** The real gate, not the field that looks like it.
- **What changed, when, and by which request?** Admin change logs, audit tables, cases and their history.
- **Is the activity real?** Real orders, bookings or events by week, against a baseline from before the problem.
- **Is a job failing?** Logs for the entity, narrowed by service first.
- **What does the customer see?** The public page, in the browser.
- **What does the code do?** Read the default branch before claiming how something behaves.

Keep going until the timeline explains the symptom. If one fact doesn't fit (activity is possible but nobody acts), say so and dig rather than smoothing it over.

## 4. Claim-check before drafting

List every claim the reply will make and tie each one to a query result, a log line, a code line or a linked message. Drop or hedge anything you can't tie. Then walk the profile's **Known traps**; every trap there was learned from a confident, wrong answer.

## 5. Draft the reply

Save it as a draft in the reporter's thread, never as a root message. If a draft is already attached there, replace it the way the profile describes. Write it the way the user would say it to a teammate:

- Tag the reporter and start with the answer in one or two lines.
- Use the domain's own terms consistently, and never a vague stand-in that could mean two states.
- When the cause is a sequence of events, give a short dated timeline. Say what each request or change did, not who did it, and link the requests.
- Hedge inferences ("I think", "it looks like"); linked facts don't need it. Short sentences, one fact each.
- Leave out internals the reader can't use (PR numbers, table names). Thank them when the report surfaced a real gap.
- End with the fix and a concrete offer, without promising actions another team owns.

## 6. Report back

Answer first in about five lines: the cause, the evidence that settles it, anything still unexplained, and the draft quoted with its link. Ask at most one question, and only for a call that is the user's to make. When the user says it's sent, read the posted message before moving on.

## 7. Log it

If the reply unblocked someone or surfaced a product gap, add one line to the career contributions log (`~/.claude/skills/flagrare/career/contributions.log.md`, format in `plugins/flagrare/lib/career/STATE.md`) when it exists. Add any new trap or query to the profile.
