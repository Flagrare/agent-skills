---
name: editorial-pass
description: Review a finished or near-finished document the way a human editor reads it, start to finish, building a model of what it's trying to communicate, then diagnosing cohesion, coherence, narrative throughline, pacing, consistency, reading fluency, contextualization, and clarity across the whole piece, never just line-by-line. Also hunts four noise categories agents habitually leave behind: provenance narration ("as verified in X", "so-and-so confirmed"), ruled-out-hypothesis residue ("we confirmed it is not Y"), self-referential scaffolding, and dramatized background (illustrating known concepts, stakes-selling, deriving what only needs asserting). Use whenever the user asks to review, edit, polish, tighten, or clean up a document, asks whether a doc "reads well", "flows", "makes sense", or "has a throughline", or before shipping any long-form prose another human will read: TDDs, RCAs, design docs, investigation writeups, READMEs, proposals, long PR descriptions.
---

# Editorial pass

Agents review documents the way linters review code: one localized finding at a time, each judged against a rule, none judged against the whole. A human editor does something different. They read the document start to finish, build a running model of what it is trying to tell them, notice where that model gets confused or bored or lost, and only then descend to the line level. Most of what makes a document fail is invisible at the line level: a section that answers a question nobody has asked yet, a term that changes meaning halfway through, a middle that sags because three paragraphs repeat one idea, an ending that pays off a promise the opening never made.

This skill is that editor. It applies to any long-form document, technical or not. Do not treat a TDD and an essay as different species: humans process both through well-sequenced steps, stakes, and payoffs. It is all storytelling, and the editor's job is the same everywhere: minimize the reader's risk and mental load in getting what the document is trying to communicate. For a technical doc that means the reader can answer *what are we solving, why, and how* without rereading.

One boundary before anything else: this is a prose editor, not a technical reviewer. You review the writing, never the work the writing describes. Whether the schema is right, the design is sound, or the numbers hold is someone else's review; your jurisdiction is whether a reader can receive what the document says. The one exception is *internal* contradiction: when the document disagrees with itself, that is a writing defect and yours to flag.

## When to invoke

Whenever a document exists and a human is going to read it: the user asks for a review, an edit, a polish, a "does this make sense" check, or a cleanup of a draft you or someone else produced. Invoke proactively after you finish drafting any long-form document, because the failure modes below are precisely the ones drafting agents introduce. For *writing* a document from scratch, `/flagrare:write-docs` owns the craft and `/flagrare:tdd-writer` owns TDDs; this skill is the read-and-repair counterpart and assumes a draft already exists.

The contract: produce the editorial memo first (step 5), get the author's go-ahead, then apply. Do not silently rewrite someone's document as step one.

## The procedure

### 1. Read the whole document. Twice.

Read the full document before writing a single note. The first read is for the felt experience, as the target reader, not as a reviewer: where did you lean in, where did attention drift, where did you have to backtrack and reread, what did you have to hold in your head unresolved and for how long. Resist the impulse to annotate on first contact. Many apparent problems resolve later in the document, and many real problems only become visible in retrospect.

When the first read ends, write one sentence: *what is this document trying to communicate?* That sentence is the spine. Everything else in the review hangs off it. If you cannot write the sentence, that inability is the primary finding and nothing at the line level matters yet.

The second read is diagnostic. Now you know what the document is trying to do, so the question becomes: where does it succeed at that, and where does it fall short?

### 2. Diagnose from large to small

Structure before flow, flow before paragraphs, paragraphs before lines. An editorial memo that opens with comma splices when the document has a broken arc wastes the author's attention. Work down through four layers:

**Throughline.** Does every section pay off the spine, or do some sections belong to a different document? Does the opening make a promise (a question, a stake, a hook) that the rest of the document keeps? Two cheap whole-document proxies: read only the headings in sequence and check whether a skim-reader could reconstruct the argument from them alone; then read only the first sentence of each paragraph and check whether they form a coherent chain on their own. Where either chain breaks, the structure is broken there, whatever the sentences say.

**Sequencing and contextualization.** A reader can only understand a sentence with what earlier sentences gave them. Walk the document asking, at each new concept, claim, or term: has the reader been given what they need to receive this, here? Context must land at the point of need, not in a glossary and not three sections late. The most common failure is curse-of-knowledge ordering: the author presents things in the order they learned them, or the order the system executes them, instead of the order a stranger can absorb them.

**Pacing and proportion.** Space in a document is emphasis. Does the amount of text each idea gets match its importance to the spine? The two standard failures are opposites: the load-bearing risk compressed into one six-clause sentence, and a minor mechanism sprawled across three paragraphs because the author found it interesting to figure out. Watch also for the sagging middle, where consecutive sections restate one idea in different clothes, and for repeated information (the same fact introduced twice usually means two drafts were merged and nobody reread the whole).

**Consistency.** One name per concept for the whole document; synonym-cycling reads as elegant variation to the writer and as a second concept to the reader. Check that numbers, claims, and terminology agree across sections, that nothing promised ("discussed below") is missing, and that tone doesn't lurch register mid-document.

### 3. Hunt the four noise categories

These are deletion passes. Agents (and tired humans) leave all three behind, and each one is the residue of the writing process showing through the shipped document. The reader is buying the building, not the scaffolding.

**Provenance narration.** How the author learned a fact is research trail, not content. "As verified in `ia-logic.js`", "X confirmed with Y in the thread", "a design doc pointed here", "checked across code, Confluence, and Slack: no such job exists". State the fact and let it stand on its own authority; the verification happened, it just doesn't need to be narrated. Words to watch: *verified, confirmed, as discussed with, per the thread, according to the doc, after checking, I looked at*.

> **Before:** Per the M1 decision doc (confirmed by the PM in the 2026-06-16 thread), `sold_out` must reset at midnight venue-local. Verified across code, Confluence, and Slack: no such reset job exists today.
>
> **After:** `sold_out` resets at midnight venue-local, and no job does that today, so an item marked "out of stock until tomorrow" never clears.

Two exceptions, both narrow. Cite a person when their *sign-off* is the pending action (an approver, an owner of an open decision), never as attribution for a fact. Keep the method when the method *is* the claim: a benchmark result is inseparable from how it was measured.

**Ruled-out residue.** Agents keep a record of the negative space around what they proved: "we confirmed the reconcile is not the cause", "this turned out to be a red herring", "no changes are needed to the serve path (verified)". The investigation needed those steps; the reader almost never does. A dead branch earns its sentence only if a future reader would plausibly walk into the same dead end and redo the work, and then it gets one line, placed exactly where that reader would start digging, not a section of its own. Everything else: keep the positive conclusion, delete the anti-thesis. "The feature is a write path; reads already work" is one sentence doing the job an entire "what needs no change (verified)" section was doing.

**Self-referential scaffolding.** The document talking about itself as a draft: "this corrects an earlier note", stale `[NEEDS VERIFICATION]` markers on things since verified, resolved questions kept as ~~struck-through~~ entries with "resolved:" annotations, a closing "verification summary" listing every source checked. A settled decision is not a question: state the choice once, where it lives, and delete the deliberation. If everything under a heading got resolved, cut the heading rather than write "N/A". The tell that this category is present: the document got *longer* on the pass that resolved things. Later passes should subtract.

**Dramatized background.** Writing that argues for what the reader only needs to accept. Three tells: an illustration of a concept the room already holds ("a 'Hamburger' is one fixed thing with no 'choose your sauce'"); a stakes sentence selling why the work matters ("customization is what makes a real menu"), when the document's existence already establishes that; and a causal chain walked step by step where only its conclusion is used downstream ("the only writer is the POS sync; manual partners have no POS; therefore they cannot author"). Assert the fact at the reader's altitude and move on; state the mechanism once, where it is load-bearing, not in the intro. The boundary that keeps this cut from gutting real context: **context is for decisions, assertion is for background.** Anything the reader must *judge* keeps its full ingredients (the current behavior, the fork, the stakes); anything the reader must merely accept to keep reading gets one plain sentence. The per-sentence test: if deleted, does the reader make a wrong decision, or just feel less escorted? Wrong decision, keep. Less escorted, cut.

### 4. Sweep for clarity

A separate lens over the same text, hunting three things: jargon a fresh reader can't decode, sentences too compressed to unpack in one breath, and phrases that sound technical but say nothing ("holds by construction", "by design", "leverage this"). Define internal jargon at first use, inline, in the same sentence; calibrate to a new hire who knows the field generically but not this corner of it. Give the densest, most important paragraph the most room: break it into beats, one idea per sentence, cause before effect. The test is reading aloud: any clause you can't say in one breath, or any term the new hire would stop to look up, is a rewrite.

Clarity is not simplification. When the accurate explanation needs the actual data model, use the actual data model; the sin is making the reader do the unpacking, not the presence of detail. Density is fine where content is genuinely parallel reference material (a column list, an appendix, an error table). That's scannable by design; don't prose-ify it.

### 5. Deliver an editorial memo, then wait

Report before rewrite. The memo, in this order:

1. **The spine, as read.** One or two sentences stating what you understood the document to be communicating. This is both the frame for everything below and a test: if your reading differs from the author's intent, that gap is the biggest finding of all.
2. **Overall diagnosis.** The one or two dominant problems, named plainly. Don't bury a broken arc under fifty line notes.
3. **Findings, large to small.** For recurring patterns, name the pattern and give two or three representative examples, not an exhaustive list of instances. Quote the actual text; propose the actual replacement for at least one example so the author can see the move, not just the rule. Organize findings by what matters to the author, not by this skill's checklist: the noise categories and layer names above are lenses for *finding* problems, and they make a poor table of contents. A memo with a section per category reads like a form being filled in; a memo ordered by "here is what will cost your reader the most" reads like an editor.
4. **Tiers.** Split into: fixes you'll apply on approval (mechanical, verified); gaps you'll mark visibly but not fabricate (a missing section becomes a `[TBD: ...]` anchor, never invented content); and judgment calls that belong to the author (cuts that trade completeness for pace, register choices).
5. **What works.** Briefly. The author needs to know what not to touch in revision.

The memo is itself a document someone reads, so it obeys its own rules. Don't narrate your procedure ("I read it twice, per the skill"), don't report checks that came back clean ("no em-dashes found"), don't pad it with everything you looked at. State findings; silence is the report for everything that passed.

Then stop and let the author respond. When they approve, apply. For structural problems prefer rewriting the document fresh over patching sentences in place: framing decisions are baked into sentence structure, and polish cannot fix a paragraph that shouldn't exist. Leave the prior version on disk for diffing.

### 6. Verify after applying

Compression and rephrasing can silently change meaning. After the rewrite, re-check every claim whose wording changed against its source (the code, the data, the referenced doc), then read the final document start to finish one more time as a stranger. For high-stakes documents, the strongest check available is a fresh reader with no context: hand the document alone to a subagent and ask what's ambiguous, what knowledge it assumes, and whether anything contradicts itself. What confuses the context-free reader will confuse the real one.

## Anti-patterns

**Localized-only review.** Jumping straight to line edits without ever forming the spine sentence. If your review could have been produced by concatenating per-paragraph reviews, you didn't read the document, you scanned it.

**Rewriting into your own voice.** The goal is the best version of *this* document by *this* author. When a change would alter meaning or intent, query instead of overriding: "did you mean X? a reader may take this as Y." Learn the difference between "this author always does X" (voice) and "this author accidentally did X here" (error).

**Nit-first memos.** Leading with typos and comma splices while the structural problem goes unnamed. One-off mechanical errors get fixed silently in the apply step; a *recurring* sentence-level pattern (comma-splice chains, over-compression, synonym cycling) is a real finding and earns its place in the memo, after the structural ones. Spend the memo on what only an editor can see.

**Playing technical reviewer.** Drifting from the text into the work: critiquing the schema, the architecture, the query plan, the estimate. However right you are, it's out of jurisdiction and it crowds the memo the author came to for a read on the writing. Flag internal contradictions; leave design review to the design reviewers.

**Deleting load-bearing negatives.** The ruled-out pass has a purpose test, not a blanket ban. An RCA's "we ruled out the deploy" can be the one line that stops the next on-call from repeating a four-hour dead end. Cut residue, keep insurance.

**Cosmetic completeness.** Filling a gap with plausible invented content so the document looks finished. A visible `[TBD]` is honest and actionable; fabricated filler is a landmine.

**Em-dashes.** House rule, enforced by hooks: never introduce one, and flag any you find. Commas, colons, parentheses, or two sentences.

## Cross-references

- `/flagrare:write-docs` teaches the writing craft this skill inspects for (reader's situation, classic style, context at point of need). Reach for it when the fix is "rewrite this section", not just "cut this noise".
- `/flagrare:tdd-writer` owns TDD authorship and carries the Restraint rules this skill generalizes; for a TDD, run it for template conformance and this skill for the read.
- `/flagrare:ticket-creator` and `/flagrare:open-pr` produce the short-form documents; the same noise categories apply there at smaller scale.

## Why this exists

The skill distills a June 2026 TDD review where the author's feedback converged on one insight: the drafting agent had been reproducing its own exploration trail instead of writing for the reader. The document was factually impeccable and exhausting to read, full of who-confirmed-what, sections proving what *didn't* need to change, and resolved questions preserved as strikethroughs. The fix was never more rules about sentences. It was reading the whole thing the way its reader would, asking what each piece contributed to what/why/how, and cutting everything whose only audience was the author. The document got shorter, and better, on every pass after that.

The review procedure itself is grounded in a survey of the published skills ecosystem ([`docs/research/2026-07-03-editorial-pass-prior-art.md`](../../../../docs/research/2026-07-03-editorial-pass-prior-art.md)): the two-read protocol and large-to-small order of attention come from fiction editing practice, the fresh-reader verification from Anthropic's doc-coauthoring skill, and the noise categories are named here because nothing in the ecosystem had named them.
