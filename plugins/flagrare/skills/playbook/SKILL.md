---
name: playbook
description: Write a playbook, a step-by-step tutorial that a non-engineer follows to use an internal tool or run an operational process (launch agents placing test orders, support agents refunding, ops checking a dashboard). It runs the real flow in dev for screenshots, quotes the UI's exact messages from the code, links every page, channel, account and dashboard it names, finds escalation paths from past Slack threads instead of asking, and writes in tutorial shape (numbered steps, one action per line, "If it says / Do this" tables), not prose. Use when the user says "write a playbook", "runbook", "guide for <team>", "how-to for agents", "training doc", or "document how to use <tool> for ops/support/launch". Not for engineering docs, TDDs or READMEs: those are /flagrare:write-docs and /flagrare:tdd-writer.
---

# Playbook

A playbook is read by someone in the middle of their job, with the tool open in another tab. They aren't studying it. They glance at it, do the next step, and glance back. So everything in it serves that glance: short steps, the exact words on the screen, a picture of what they should be seeing, and a link wherever they need to go.

The usual failure isn't wrong content, it's the wrong shape. A playbook written as paragraphs is correct and goes unread. "People hate big fat paragraphs. This should feel like a tutorial."

## The shape

Use this structure, and the same section names, unless the flow really doesn't fit:

1. **Title:** what the reader does, as a verb ("Placing and cancelling test orders from Admin").
2. **When to use it:** one line, plus a two-bullet list of the situations.
3. **Stakes callout:** one red callout for the thing that costs money or trust when it goes wrong ("A test order is a real order. The partner gets paid unless you cancel it."). One only.
4. **Before you start:** 2 to 4 bullets covering access, accounts, and who to tell first.
5. **Numbered steps.** Each one is a `##` heading starting with a verb ("## 2. Pick an item"), then a numbered list with one action per line, then a screenshot.
6. **"If it says / Do this" tables**, one per screen state that shows messages (errors, warnings, failures). Column 1 is the first words of the message, column 2 is the action. Add a "Try again?" column where a retry can do harm.
7. **Recovery paths:** the ways to undo or fix things (cancel from another screen, find the thing you lost), as sub-steps (5a, 5b).
8. **Recurring check:** the daily or weekly review, if there is one. Give each list on the dashboard a row: what it shows, what to do.

Rules for every line:

- **One action per list item.** "Click **Cancel order**." not "Open the order page and cancel it with the right reason."
- **Short sentences.** If one needs a comma and "and", split it.
- **No paragraphs over two sentences.** Anything longer becomes a list or a table.
- **Bold the exact UI label** the reader clicks or reads: **Place order**, **"Cancellation sent"**.
- **Captions are one short line** saying what to look at: "Pick the first one: CP cancelled." Don't describe the whole screenshot.
- **Each fact appears once.** If the stakes callout says it, the steps don't repeat it.

Field-tested the hard way: the first draft of the SKU test order playbook was correct, illustrated, and still rejected for being prose. The editorial pass made it more coherent, and it was rejected again for being verbose. Then it was rewritten in the shape above and came out half as long. Draft in this shape from the start, and don't polish your way toward it.

## Get the facts from the source

### The UI copy

- **Read the messages from the code**, not from memory or the design doc: error strings, warnings, button labels, dialog titles. The tables quote them, so they must match the screen word for word.
- **Walk the adjacent screens too.** The reader's recovery path often runs through a screen the feature didn't build, and that's where the traps are. Example: the order page's cancel dialog lists "CP cancelled full payout" right under "CP cancelled", and the full payout one pays the partner. That trap earned its own red callout.
- **Note what blocks and what only warns.** Red and yellow need different tables.

### Links

Link everything you name. A reader who has to search for a page drops the playbook.

- Admin and app pages get **prod URLs**. Take the URL format from the codebase's routes, or from links the team already builds (a dashboard query, a Slack message), never by guessing.
- Slack channels get links. Accounts and records get a link to their admin page.
- Dashboards get links, plus which filter or environment to choose.
- Before handing over, list every noun in the playbook that names a place, and check each one has a link.

### Escalation paths

Every "report it" or "ask someone" needs a destination. **Find it, don't ask the user:**

- Search Slack for the account id, the error text, or the problem ("no credit price", the test account's user id). Look for where similar problems were raised before and who answered.
- Prefer the team's existing intake channel or form (a `#...-support` channel with a submission template) over a squad channel. That's where the people who act on it already look.
- In your summary to the user, cite the precedent thread for each path, so they can check it.

### Settled facts

Before asking the user anything (which account, which environment, who owns what), search the session, the design doc, the tickets and memory. Asking about something already decided costs trust. "We have been through this dude."

## Screenshots

- **Run the real flow end to end in dev:** place the order, cancel it, trigger the error. Screenshot each state the steps mention. Clean up afterwards (cancel what you created) and say so.
- **Never use production data with real customers on it.** Dev or staging only.
- **Crop to the part that matters** (`sips -c <h> <w> --cropOffset <y> <x>` on macOS). A dialog crop beats a full-page shot.
- **Show the data.** If the default view is empty (prod has no rows yet), switch to an environment that has rows, and say which one in the caption.
- **Page behind a login:** open it in a visible tab and ask the user to log in. Don't skip the screenshot, and don't type credentials yourself.
- **Notion:** upload each image with the file-upload flow (`create-file-upload`, then a multipart POST of the file), then reference the returned `file-upload://` source in an image block.

## Open decisions

Sometimes the playbook needs a rule nobody has decided yet ("how long to wait for the partner to confirm"). Don't invent it, and don't settle it with the user unless it's theirs to decide.

- Put it in a visible callout addressed to the team that owns it: "Open question for Partner Launch: …".
- Leave it in the published page. That's how the owners see it.

## Publishing

1. Draft it as a **private** page (Notion: `creation_mode: "draft"`), so the user reviews it before anyone else sees it.
2. Run `/flagrare:editorial-pass` with a bias toward **cutting**. Any finding that adds words needs a strong reason.
3. On approval, move it **next to the related design doc or TDD**, and link it from the ticket that tracks it.
4. Replace any "draft notes" callout with a one-line notice if something is still true for readers ("The tool isn't in prod yet. Screenshots are from dev."), or delete it.

## Self-check before handing over

- [ ] Every step is a numbered list with one action per line. No paragraph runs over two sentences.
- [ ] Every message in a table is quoted from the code.
- [ ] Every named page, channel, account and dashboard is linked.
- [ ] Every "report it" or "ask" has a destination backed by Slack precedent.
- [ ] Every screen the steps mention has a cropped dev screenshot with a one-line caption.
- [ ] Traps on adjacent screens are called out where the reader meets them.
- [ ] Open decisions are callouts addressed to their owners.
- [ ] No em dashes.

## Cross-references

- `/flagrare:write-docs`: the craft layer (reader's situation, plain words). This skill fixes the shape for the how-to case.
- `/flagrare:editorial-pass`: the review pass. Run it after drafting, biased toward cutting.
- `/flagrare:smoke-test`: when you run the flow for screenshots and find a bug, fix or report it before documenting around it.
