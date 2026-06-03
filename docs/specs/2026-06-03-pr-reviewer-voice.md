# PR Reviewer: Friendlier Inline Comments

**Date:** 2026-06-03
**Status:** Approved (pending implementation plan)
**Affected skill:** `plugins/flagrare/skills/pr-reviewer/SKILL.md`

## Why

The `/flagrare:pr-reviewer` skill drafts inline GitHub comments that the user pastes into PR reviews. The current SKILL.md already prescribes a friendly voice, with lines like "Sound like a friendly teammate, not a bot or a gatekeeper" and "Sound conversational." Despite those rules, the comments it actually produces read as cold, clipped, and sometimes faintly aggressive. The author reports they don't sound like a person writing to another person.

That tells us the existing rules aren't doing the work we hoped. They're abstract, they sit alongside other rules in a long bulleted list, and the model interprets "be conversational" in its own way (usually as "be terse but use contractions").

The fix is to stop relying on abstract warmth rules and instead show the model exactly what we want, with concrete before-and-after pairs. This mirrors the approach that worked for the tutor skill, where Lane Wagner's research at boot.dev was clear: a one-sentence negative example moves the model more reliably than a paragraph of abstract guidance. The catalogued findings live at [`docs/research/2026-05-28-boots-ai-tutor-design.md`](../research/2026-05-28-boots-ai-tutor-design.md).

## Scope

Only the inline GitHub comment text changes. The wider review output (the severity-labeled finding list in Claude Code, the overall assessment, the section headings) stays structured, because the user wants it scannable for triage. The change is targeted at the part of the output that gets pasted into GitHub and read by another human.

## What stays from the current Step 5

These rules are still useful. They guard against real failure modes that the new content doesn't address.

- 1-2 sentences max for inline comments.
- Copy-paste ready for GitHub.
- No AI-isms: avoid "consider", "it would be beneficial", "enhance", "leverage", "crucial", "pivotal".
- Reserve firm language for actual blockers only.
- No em dashes. Use commas, periods, or parentheses.
- No rule of three.
- No "Additionally", "Furthermore", "Moreover".
- No sycophancy ("Great approach!", "Excellent work!").
- Be specific. "Add a null check here" beats "It might be worth considering adding a null check to improve robustness."

## What gets removed

These two lines get cut because they're the abstract prescriptions that aren't producing the warmth the author wants:

- "Sound like a friendly teammate, not a bot or a gatekeeper."
- "Sound conversational. 'Pretty sure this is a typo' beats 'Table name typo: it is X everywhere else in this repo.'"

The work those lines were trying to do gets handled by the new sub-section below, using concrete examples instead of abstractions.

## What gets added

A new sub-section called **Voice and examples** sits between "Comment requirements" and "Humanization rules" in Step 5. It has three pieces: a short persona framing at the top, eight before-and-after pairs in the middle, and a six-bullet list of recurring patterns at the bottom.

### Persona framing

This sits at the top of the new sub-section and primes the voice the model writes in.

> **Voice setup.** Think of the author as a teammate you respect, someone who's going to read this tomorrow morning before they've had coffee. They already shipped a draft, which took real effort. Write the way you'd actually talk to them at lunch. Usually that means starting from what we noticed rather than what we want done, and asking instead of telling when we're not sure. Use "we" where it fits, since the code is something we share.

### Eight before-and-after pairs

Each pair shows the comment text only. The envelope around it (`SEVERITY - path L##` and the `GitHub comment:` prefix) stays the same as it is today. The pairs are ordered by severity, then by finding type, so the model sees a critical-bug example first and a small nice-to-have example last.

**1. Null check (Critical, correctness)**
- Cold: `` `venue` can be null here. Add a safe call or null check. ``
- Friendly: `` I think `venue` can come back as null here, in the case where the search doesn't find a match. We hit something similar in BookingRepo a little while ago. Should we add a guard for it? ``
- *What changed: opens with the observation rather than the instruction, frames the codebase as shared, asks instead of commanding.*

**2. SQL injection (Critical, security)**
- Cold: `SQL injection risk. Use parameterized queries.`
- Friendly: `` Heads up, looks like `userId` is going straight into the query string here. Should we switch this over to a parameterized version? It's an easy thing to miss in review. ``
- *What changed: warmer opener, asks rather than commands, "easy to miss" removes blame.*

**3. Test coverage (Suggestion, tests)**
- Cold: `Missing test for the cancelled path.`
- Friendly: `Looks like we're already covering the success and reschedule paths, but not cancel. Would be good to lock that one down too if we get a chance.`
- *What changed: credits existing work first, uses "we" throughout, "if we get a chance" softens the suggestion.*

**4. Single responsibility (Suggestion, SOLID)**
- Cold: `This method has too many responsibilities. Extract validation.`
- Friendly: `I noticed this one's doing both validation and persistence. Pulling validation out into its own function might make the tests easier for us down the line. Totally up to you, though.`
- *What changed: names the two responsibilities specifically, explains why with "us", explicit "up to you" defuses authority.*

**5. Missing edge case (Suggestion, correctness)**
- Cold: `` What happens when `items` is empty? Add handling. ``
- Friendly: `` I was wondering what happens here if `items` comes through empty. Does the totals calc just zero out, or do we want to throw? Either way is fine, just wanted to make sure whatever we end up with is intentional. ``
- *What changed: poses as a genuine question, offers both options so the author isn't cornered, "we want to" instead of "you should".*

**6. Generic naming (Suggestion, clean code)**
- Cold: `` `data` is too generic. Rename. ``
- Friendly: `` I think this `data` could probably use a more specific name, maybe something like `customerLoyaltyRecord` or whatever fits the actual shape. Future-us would probably thank us when we're grepping for it in six months. ``
- *What changed: "Future-us" is the small but real win. Concrete alternative offered, future-pain rationale frames it as shared.*

**7. Magic number (Nice, clean code)**
- Cold: `` Replace magic number `86400` with a named constant. ``
- Friendly: `` Small thing, but `86400` would probably read more clearly as `SECONDS_PER_DAY`. Takes a beat to recognize it otherwise. Worth pulling out into a constant? ``
- *What changed: "small thing" calibrates severity, admits the inference ("takes a beat"), asks instead of instructs.*

**8. Convention match (Nice, clean code)**
- Cold: `Use early return.`
- Friendly: `` Heads up, the rest of `BookingService` is going with early-returns on validation failures. Might be worth doing the same here, just for consistency. ``
- *What changed: references the local convention without claiming authority, "might be worth" hedges.*

### Six-bullet patterns list

This sits under the pairs and gives the model something to check itself against when the finding doesn't quite match any of the eight pairs.

> **What the pairs are showing:**
> - Open with what we noticed, not what we want done.
> - First-person voice when we're guessing ("I think", "looks like", "wondering if").
> - "We" instead of "you" when the codebase is the subject.
> - One short clause of "why" attached to suggestions, not a paragraph.
> - Hedges: "probably", "might be worth", "totally up to you", "if we get a chance".
> - Severity in the opener: "Heads up" for must-fix, "small thing" or "would be good" for nice-to-haves.

## One more change in the same area

The current SKILL.md has a "Format per finding" block right after the Humanization rules (around lines 200-209 of the existing file). It demonstrates the output envelope using three example comments, and those example comments are written in the old cold voice. If we leave them, the model would see a cold reference example right after reading the new friendly pairs, which is the kind of mixed signal we want to avoid.

The three example comments should get updated to match the friendly voice. The envelope around them stays the same. The new versions:

```
CRITICAL - `path/to/File.kt` L45
GitHub comment: I think `venue` can come back as null here when the search doesn't find a match. Should we add a guard for it?

SUGGESTION - `reservations/BookingService.kt` L32
GitHub comment: I noticed this method's doing a fair bit. Pulling validation out into its own function might make the tests easier for us. Totally up to you.

NICE - `reservations/BookingServiceTest.kt` (file-level)
GitHub comment: Would be good to add a test for the cancelled path too, if we get a chance.
```

These three intentionally don't repeat the exact phrasings from the eight pairs above. They're variations on the same voice, so the model sees that the patterns can flex rather than getting trained to copy specific sentences word-for-word.

## Out of scope for this change

A few things that came up during brainstorming but aren't part of this work:

- The severity-labeled finding list in Claude Code keeps its current structured format. The change is only about the comment text that gets pasted to GitHub.
- The overall assessment paragraph, the context-fetched block, and the checklist all keep their current voice. The author may revisit those later if they feel cold in practice, but they're out of scope here.
- No changes to which subagents run, what they look for, or how findings get synthesised. The voice change is purely at the drafting layer.
- No changes to severity calibration. CRITICAL still means must-fix, SUGGESTION still means should consider, NICE still means optional.

## How we'll know this worked

The clearest signal is the em-dash ban. The current SKILL.md already says "No em dashes" in inline comments, and the model isn't reliably honouring that. If after this change the model stops using em-dashes in drafted comments, we'll have evidence that the new structure (pairs and persona framing) is doing real enforcement work that the old abstract rule wasn't.

The softer signal is whether the author still finds the comments cold when they review them. That one is subjective and gets evaluated in real use, not in a controlled test.

## Failure modes to watch for

A few things that might show up once this ships:

- The model might pick up the voice from one pair (say, pair 5's "I was wondering") and over-use that exact phrase across every comment. If that happens, the fix is to vary the openers across pairs more explicitly, or add a rule about not starting two adjacent comments the same way.
- The "we" voice could feel weird when the reviewer is a contractor or an external collaborator who doesn't actually share the codebase. We're treating that as an acceptable edge case for now, since the skill is mostly used by team members reviewing each other's work.
- The persona framing assumes the author is on the same team. If the skill ends up being used for open-source review (where the reviewer and author may never have met), the persona may need a second variant. Out of scope for v1.

These are observation hypotheses, not predicted bugs. The patterns list at the bottom of the new sub-section is the place to grow if real failures appear.
