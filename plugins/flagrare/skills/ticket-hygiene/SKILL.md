---
name: ticket-hygiene
description: "Match the user's tickets with the real state of their work and fix the gaps. Pairs every open ticket assigned to the user with its PRs (open, draft, merged, closed), works out the stage the work is really at (started, in review, merged, done), and shows each ticket's status next to the one it should have. Forward moves backed by a PR are applied right away; done, reopened, unassigned and stale tickets are proposed. Also takes one ticket (`SKU-123`) or an event (`merged SKU-123`, `deployed SKU-123`). Use when the user says 'ticket hygiene', 'sync my tickets', 'are my tickets up to date', 'move my tickets', 'fix ticket statuses', 'the PR merged', 'it's deployed', or right after a merge or deploy of their work. Also for a scheduled hygiene run, which only reports."
---

# Ticket hygiene

The board should show what is really happening. This skill reads the user's tickets and PRs, pairs them, and moves each ticket to the status its work is at. It is the place where merges and deploys get reflected, since no other skill runs at those moments.

**REQUIRED BACKGROUND:** read `<plugin root>/lib/tickets/LIFECYCLE.md` first, the plugin root being two directories above this skill's base directory. It defines the stages, how a stage maps to a real status, and the rules every move follows. This skill does not repeat them.

## Modes

- **Sweep** (no args): every open ticket assigned to the user, plus every ticket the user's recent PRs mention.
- **One ticket** (`SKU-123`): the same checks for that ticket only.
- **Event** (`merged SKU-123`, `deployed SKU-123`, `verified SKU-123`): the user is telling you something happened. Use it as evidence for that ticket, then run the one-ticket checks.
- **Scheduled** (started by `/loop`, a schedule or another agent, or args contain `scheduled`): run the sweep, write nothing, and list the moves for the user.

## Step 1: Load the config and the tracker

Read `~/.claude/skills/flagrare/config.json` (`github_login`, `repo_scope`, and the `tickets` block). Find the tracker MCP or CLI the same way `/flagrare:intake` Step 0 does. With no tracker reachable, say so in one line and stop.

## Step 2: Collect tickets and PRs

Run these in parallel.

**Tickets.** Open tickets assigned to the user, not in a Done-category status.
- Jira: `assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC`
- Linear: assignee is me, state type not `completed` or `canceled`
- Others: the equivalent filter

**PRs.** The user's PRs in the configured repo scope:

```bash
gh search prs --author "@me" --owner <org from repo_scope> --state open --json number,title,url,isDraft,repository,updatedAt --limit 50
gh search prs --author "@me" --owner <org from repo_scope> --merged-at ">=<14 days ago>" --json number,title,url,repository,closedAt --limit 50
gh search prs --author "@me" --owner <org from repo_scope> --state closed --closed ">=<14 days ago>" --json number,title,url,repository,closedAt --limit 50
```

Get each PR's branch name with `gh pr view <url> --json headRefName,body,mergeCommit`. Closed PRs that also appear in the merged list are merged, not abandoned.

**Deploy evidence**, for merged PRs only: did a release or deploy run that holds the merge commit finish? Check the repo's release workflows (`gh run list --commit <merge sha>` or the runs created after the merge), or the deploy tool the user has connected. Record "deployed" only with a finished run or the user's word. "Verified" needs a check in production, or the user saying it works there.

## Step 3: Pair them

A PR belongs to a ticket when the ticket key appears in its branch name, title or body. Use the project keys from the tickets in Step 2 to build the pattern (`\b(SKU|IOPS)-\d+\b`). One ticket can have several PRs and a PR can mention several tickets; keep all the pairs.

Then work out each ticket's stage from its PRs, using "What stage the work is at" in LIFECYCLE.md.

**Epics and parent tickets are out.** Their status follows their children and the team lead usually moves them, so never move one and never flag one as stale. Leave them out of the table.

## Step 4: Decide the action for each ticket

| Situation | Action |
|---|---|
| A PR backs a forward move to `started` or `in_review` | **Apply** |
| All PRs merged, `merged_auto` is true | **Apply** |
| All PRs merged, `merged_auto` is false or unset | **Propose** (the first time, also ask whether to make it automatic, and store the answer) |
| Merged, deployed and verified | **Propose** `done`, quoting the evidence |
| Merged and deployed, not verified | **Flag**: say what check would prove it works |
| Every PR closed without merging | **Propose** `reopened`: back to its earlier status, or the user's choice |
| Ticket is `started` or later, no PR, nothing touched it in 5 working days | **Flag** as stale |
| Ticket is `in_review` or later but has no PR at all | **Flag**: a PR may be missing the key |
| PR with no ticket key | **Flag**: the PR needs a ticket |
| Ticket unassigned but a user's PR references it | **Propose** assigning it to the user |
| Ticket already at or past the expected stage | Nothing |

Map every target stage to a real status with "Picking the real status for a stage" in LIFECYCLE.md, and follow its rules on every move (own tickets only, read before writing, forward only).

## Step 5: Show the table, apply, ask

Show one table, then act. Skip tickets that need nothing.

```
| Ticket | PR | Now | Should be | Action |
|---|---|---|---|---|
| [SKU-123](url) Menu disabled state | [#481](url) open | To Do | Needs Code Review | moved |
| [SKU-130](url) Payout export | [#490](url) merged Nov 10, deployed | Needs Code Review | Ready to Release | moved |
| [SKU-131](url) Report email | [#495](url) merged, deployed, checked | Ready to Release | Finished | proposed |
| [SKU-140](url) Image upload | none, quiet 6 days | In Progress | ? | stale |
```

Apply every **Apply** row (in a scheduled run, mark them "would move" instead). Then ask about the **Propose** rows in one `AskUserQuestion` with `multiSelect: true`, one option per move, and apply the ones the user picks. **Flag** rows need no answer; they stay in the table.

Close with one line: how many moved, how many are waiting on the user.

## Anti-patterns

- **Don't move a ticket to done on a merge or a deploy alone.** Done needs proof the change works in production. Field-tested the hard way: two tickets went to Finished right after the user said "Deployed", and the next message was "but did you test/check?".
- **Don't pick a status by its category.** "Ready to Release" sits in the In Progress category in Jira, so a category match puts merged work back in the in-progress column.
- **Don't override a teammate.** A ticket already past the expected stage stays there, even with a status this skill would not have picked.
- **Don't ask about the automatic moves.** A PR opened or a ticket started is not a question. Asking about them is the noise this skill exists to remove.
- **Don't touch anything but assignee, status and sprint.** Comments and descriptions still need the user's OK.
- **Don't write in a scheduled run.** Nobody is there to catch a wrong move.

## Flow position

```
/flagrare:work-prep    → started      (automatic, through intake)
/flagrare:open-pr      → in_review    (automatic)
[PR merges]            → merged       /flagrare:ticket-hygiene
[deploy + check]       → done         /flagrare:ticket-hygiene (asks)
/flagrare:standup-report flags mismatches and points here
```
