---
name: fact-check
description: Verify every claim in a finding, report, chat draft, PR description or reply before it reaches the user or anyone else, by re-checking each one against its primary source (the code on the main branch, a fresh query, the message itself, the live page). Run it on your own, without being asked and without asking permission, whenever you are about to (a) give the user a conclusion, cause, number or "X happened because Y", (b) save or post a draft in the user's name, (c) relay findings from a subagent, a fork, a delegated worker or a bot. Also trigger when the user says "fact check", "are you sure", "check your claims", "verify this", "is that true".
---

# Fact check

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. See `/flagrare:write-docs`.

Users end up asking "are you sure?" and "fact check everything" because answers arrive with claims nobody re-checked. This skill makes the check automatic. It is not a question to ask the user: it is a step you run before you answer.

## Settings

How to reach each source is specific to the user's company, so it lives outside the plugin, in `~/.claude/skills/flagrare/fact-check/sources.md`. Read it at the start of every run.

If it doesn't exist, build it once before checking:

1. **Harvest what's already known.** Read `~/.claude/skills/flagrare/config.json`, the support-triage profile and recipes (`~/.claude/skills/flagrare/support-triage/`) if present, the project's `CLAUDE.md` and any saved memories about data or tool access. Look at the connected MCPs and CLIs.
2. **Ask only for the gaps**, one short question at a time, with a default offered:
   - How should data be read: a warehouse CLI, a BI tool, or a delegated agent? (Default: the connected warehouse tool.)
   - How should chat be read: which tool, and is any other tool off limits? (Default: the connected chat tool.)
   - Which web apps hold the live state people ask about, and what are their URLs?
   - What is the main branch of the repos? (Default: `origin/main`.)
3. **Write `sources.md`** with one short section per source: Code, Data, Chat, Tickets and docs, Meetings, Live apps. Then tell the user in one line what you saved and continue with the check.

Add to it when a check teaches you something, like a field that looks meaningful but isn't, or a tool that returns stale data.

## When it runs

Before any of these leave you, every time, unasked:

- A conclusion, a cause, a number, a count, a date, a name, a "who did it".
- A draft in the user's name (chat, PR, ticket, doc, email).
- Findings relayed from a subagent, a fork, a delegated worker or a bot. Their output is a lead, not a fact.

## How

1. **List the claims.** Every sentence that states a fact, in the text you are about to send. Include numbers, "only", "all", "never", "nobody", causes, and the names of people, tickets and customers.
2. **Check each one at its source, fresh.** Not from memory, not from an earlier summary, not from another agent's report. Use the access paths in `sources.md`.
   - Code: fetch and read the main branch (or the PR diff) at the cited lines. Follow the call chain until the behavior is proven, not just the line that looks right.
   - Data: re-run the query yourself and keep it. A number you can't reproduce is unverified.
   - Chat, tickets, docs, meetings: read the message, ticket, page or transcript itself. Read the whole thread, including what the other people concluded, before claiming something is new.
   - Live apps: open the page and look.
3. **Classify each claim:**
   - **Confirmed**: you saw it at the source now. Note where (file:line, query, permalink).
   - **Corrected**: the source says something else. Fix the text.
   - **Unverified**: you could not check it. Either keep checking (step 4) or drop it from anything outward. Never ship it with a hedge as a substitute for checking.
4. **Close the gaps yourself.** If something is unverified and it can be checked, check it before replying. Do not ask the user "should I check it?". The answer is always yes. Only stop when the check is impossible (no access, needs a login), and then say exactly what is missing.
5. **Then answer.** Lead with the corrected conclusion. Mention only what changed (corrections) and what truly could not be verified. Don't list everything that was fine unless the user asked for the full check.

## Rules

- Prior work by teammates counts as a source. Before calling a finding new, read what the people in the thread already found and build on it (name them).
- A subagent saying "I verified" is not verification. Re-check the claims that matter.
- Don't ask follow-up questions whose answer is obvious ("should I verify X?", "should I check the other N?", "should I fix it?"). Do it.
- Drafts still need the user's OK to send. Checking them doesn't.
- Keep the reply short: answer first, corrections, then at most one question that is genuinely the user's call.
