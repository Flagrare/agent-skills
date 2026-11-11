# Ticket lifecycle

A ticket's status should say what is happening to the work. When the board says "To Do" while a PR is in review, the team plans around the wrong picture, and the person doing the work has to remember to fix it by hand. Every flagrare skill that moves work forward moves the ticket in the same step, using the rules below.

Skills refer to this file as `<plugin root>/lib/tickets/LIFECYCLE.md`, the plugin root being two directories above the skill's base directory.

## The stages

Trackers name their statuses differently, so skills work in five stages and map each one to a real status per project.

| Stage | It means | Moved by | Moved how |
|---|---|---|---|
| `started` | Someone is working on it | `/flagrare:work-prep` (through intake, right after the ticket is read), `/flagrare:wrap-up` if it was missed | Automatic |
| `in_review` | A PR is open and waiting for review, draft or not | `/flagrare:open-pr`, right after `gh pr create` | Automatic |
| `merged` | Every PR for it merged, not deployed yet | `/flagrare:ticket-hygiene` | Automatic when `merged_auto` is true, otherwise proposed |
| `done` | Deployed and checked in production | `/flagrare:ticket-hygiene` | Always proposed, never automatic |
| `reopened` | Its only PR closed without merging | `/flagrare:ticket-hygiene` | Always proposed |

The order is `to do < started < in_review < merged < done`. Moves only go forward. `reopened` is the one backward move, and only the user can approve it.

Changes requested on a PR keep the ticket at `in_review`: the PR is still the place where the work happens.

## What stage the work is at

Read it from the PRs linked to the ticket (the key in the branch name, PR title or PR body):

- **No PR, but the user started it** (work-prep ran, a branch exists, commits reference it): `started`.
- **At least one PR open, draft or not**: `in_review`.
- **Every linked PR merged**, and no deploy evidence: `merged`. If the user said more PRs are coming for this ticket, it stays where it is.
- **Merged, the deploy that holds the merge commit finished, and a check showed the change working in production**: `done`. A deploy alone is not a check: "deployed" means it is running, not that it works.
- **Every linked PR closed without merging**: `reopened`, proposed.

## Picking the real status for a stage

1. Read the ticket's current status and the moves the tracker allows from it (Jira: list the issue's transitions; Linear: the team's workflow states; others: their equivalent).
2. Look for a cached name in `tickets.status_map.<project>.<stage>` in the shared config (below). If the name is cached and a move to it is available, use it.
3. Otherwise match by name, ignoring case:
   - `started`: In Progress, Doing, Started, In Development
   - `in_review`: Needs Code Review, In Review, Code Review, Review, PR Open
   - `merged`: Ready to Release, Merged, Ready for Deploy, Awaiting Deploy
   - `done`: Finished, Done, Released, Closed, Complete
4. Match on the name, not the category. Jira gives In Progress, Needs Code Review and Ready to Release the same category (In Progress), so the category cannot tell them apart. Use the category only to rule things out: never pick a Done-category status for `started`, `in_review` or `merged`.
5. Exactly one match: use it and cache it. None or several: ask the user once with `AskUserQuestion`, listing the statuses the tracker offers plus "Skip this stage for this project", and cache the answer. A cached `null` means the project skips that stage.
6. Some workflows have no review status (an ops board going To Do, Dev Complete, Needs QA). Map `in_review` to its "dev finished" status if the user agrees, or skip it. Never move a ticket to a status that means something else just to have moved it.

## Rules on every move

- **Only the user's own ticket.** It is assigned to the user, or it is unassigned and the user is starting it now, in which case assign it to them first. A ticket assigned to someone else gets a one-line note, not a move.
- **Only assignee and status** (and the sprint, when `add_to_active_sprint` is on). Description, comments, labels and every other field still need the user's OK.
- **Work tickets only.** Epics and parent tickets follow their children; leave them alone.
- **Read the status right before writing.** A teammate may have moved it a minute ago.
- **Forward only.** If the ticket is already at or past the target, leave it, even when the status is not the one this file would pick. A teammate's status wins.
- **Say it in one line** after moving: `SKU-123: To Do → In Progress`.
- **Never block the main task.** If the tracker is not reachable, say so in one line and carry on with the plan or the PR.
- **Scheduled runs never write.** A run started by `/loop`, a schedule or another agent lists the moves it would make and leaves them for the user.

## Shared config

The cache lives under a top-level `tickets` key in `~/.claude/skills/flagrare/config.json`, next to the other shared keys. Read the whole file, change only the `tickets` block, and write it back.

```json
{
  "tickets": {
    "merged_auto": false,
    "add_to_active_sprint": false,
    "sprint_board": null,
    "status_map": {
      "ENG": {
        "started": "In Progress",
        "in_review": "In Review",
        "merged": "Ready to Release",
        "done": "Done"
      },
      "OPS": { "in_review": "Dev Complete" }
    }
  }
}
```

- `merged_auto`: move a ticket to `merged` without asking once all its PRs merge. Ask the user the first time a ticket reaches `merged` and store the answer.
- `add_to_active_sprint` and `sprint_board`: when a ticket reaches `started` and the tracker has sprints, put it in the active sprint of that board if it is not in one.
- `status_map`: one entry per project key. Missing stages are found by name and cached the first time they are needed.
