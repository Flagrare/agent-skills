---
name: doc-edit-check
description: Check one edit to a document (a rewritten paragraph, a new section, a review fix) for the problems that whole-document reviews catch too late. It looks at the changed text and the section around it for noise agents leave behind (provenance narration, ruled-out residue like "needs no change", self-referential scaffolding, dramatized background), text written for the author instead of the reader, details said twice, broken references after a rename or renumber, contracts named but not shown, made-up examples, bare identifiers, and comment threads the edit detaches. Pair it with /flagrare:controlled-english on every edit: this skill decides what the edit should say, controlled-english fixes how each sentence says it. Use before writing any change into a design doc, TDD, RCA, README or shared page, after each review fix, and whenever the user says "check this edit", "is this paragraph ok", "doc edit check", or points at a passage that reads badly.
---

# Doc edit check

> **No em-dashes.** Nothing this skill writes may contain an em-dash; use a comma, colon, or parentheses instead. See `/flagrare:write-docs`.

`/flagrare:editorial-pass` reads a whole document once it is nearly done. Most damage happens earlier, one edit at a time. A review fix adds a sentence that makes sense alone. The next fix renumbers a section. A third one records a worry that turned out to be false. Each edit looks fine, and after a few rounds the section is dense, repeats itself and points at things that moved. This skill runs the editor's checks on each edit, so the document never drifts that far.

## When to run

Run it on every edit to a document other people will read, before the edit is written to the shared copy:

- a paragraph, bullet, table or diagram you add, rewrite or delete,
- a fix that answers a review comment,
- a rename, a renumber or a move of a section.

Then run `/flagrare:controlled-english` on what survives. Order matters: this check can delete a sentence, and there is no point polishing a sentence that should not exist.

## Scope

Read three things, not the whole document:

1. **The edit**: the old text and the new text.
2. **Its section**: from the section heading to the next heading at the same level, so you see the edit the way a reader meets it.
3. **Everything that points at it**: search the document for the section number, the names, the numbers and the claims the edit touches.

## The checks

Go through them in order. Each finding names the sentence, the problem and the fix.

### 1. Written for the reader, not for you

By the time you edit, you know the code and the plan, and the reader knows neither.

- **Answer first.** The section opens with the answer to the reader's question ("why do we need a URL at all?"), stated plainly. Do not print the question as the opener.
- **Meaning before code names.** Hide every function, table and field name in the section. If what is left does not say what happens and why, rewrite it.
- **Terms explained where they first appear**, in the sentence that uses them, not in a table cell or a list of goals.

### 2. Noise the edit added

- **Provenance narration.** "As verified in X", "so-and-so liked it", "per the meeting". State the fact. Link the source if the reader needs it.
- **Ruled-out residue.** A worry the edit disproved: "this needs no change", "it doesn't fail as not found", "we confirmed it is not Y". Delete it. Keep one line only if a future reader would walk into the same dead end, and then state it as the positive fact ("a gap in the positions doesn't change the sort").
- **Self-referential scaffolding.** "I updated", "now", "this corrects", "(new)", leftover TBDs, notes about the review. A settled decision is stated once, as the way things are.
- **Dramatized background.** Selling the stakes, or walking a causal chain step by step when only its conclusion is used. Assert it in one sentence.
- **Small gaps that do not matter.** A missing frame for one breakpoint, a TBD for a minor screen state. If the experience is not radically different, leave it to design and the tickets.

### 3. Said once, where it belongs

- A detail, a number or a reason lives in the one section that owns it. Other sections state their own point and link.
- The prose does not repeat what the diagram right above it already shows.
- The edit does not restate the reviewer's comment.

### 4. Still true everywhere

- **References.** After a rename, a renumber or a move, every "§5.4", "App. E", ticket and section link still points at the right place. Search for the old number.
- **Claims elsewhere.** If the edit changes a fact (a limit, a flow, what happens on delete), search the document for the old version and fix or remove it. Decisions, tests, rollout, monitoring and the appendix are where stale copies hide.
- **Counts.** "Four rules apply" after a rule was cut.

### 5. Concrete and real

- **Contracts shown, not named.** If the edit mentions a message, a call or a request body, show its shape (JSON, proto, SQL) and the outcomes (a small table of cases and results), or link to where they are shown.
- **Examples are real.** An example id, path or value uses the real format from the code. A made-up `"abc_1"` where the code generates `abcgrp_<KSUID>` is a finding.
- **Every claim checked at its source.** Pair with `/flagrare:fact-check` for anything new.

### 6. Formatting that reads

- **Identifiers in code format**: service names, tables, fields, functions. A sentence never starts with a lowercase identifier. Put a phrase first, or use "That service".
- **No bare labels.** Section numbers, appendix letters and ticket keys are links, with the name when it helps ("Appendix E: Future work").
- **Placeholders render.** Angle brackets can show up as `&lt;id&gt;` in some editors. Prefer `{id}`.
- **Visuals on top.** A diagram goes above the prose it explains. For one flow in time order, a sequence diagram. For a whole-feature overview with many actors, a flowchart with a legend.

### 7. Comment threads

In a collaborative editor, inline comments are anchored to text. Deleting or replacing the anchored text detaches the thread: the comment still exists, but it no longer shows next to anything.

- Before you change anchored text, keep at least part of it inside the anchor, or move the anchor to the text that now carries the point.
- After the edit, check that every thread that pointed into the section still points somewhere sensible. Re-attach any that do not.

## Output

When you run it on your own edit, fix the findings and write the result. Report in one or two lines what you changed and why, naming the check ("ruled-out residue", "said twice").

When the user asks you to check a passage, list the findings first, most serious first, each with the sentence, the problem and the fix in one line. Then offer to apply them.

## Credits

The noise categories come from `/flagrare:editorial-pass`. The reader-first, say-once, formatting and comment-thread checks come from repeated review feedback on design docs written with these skills.
