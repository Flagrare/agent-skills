# Severity rubric

Three values: `High`, `Medium`, `Low`. The point of a small ladder is forcing real prioritisation — the team will not act on a 47-row Medium list, but they will act on 4 Highs.

## High

The finding meets at least one of:

- **Blocks** the user from completing a primary task (e.g. submit button covered by a tooltip; required field with no input affordance)
- **Punishes** the user for doing the right thing (e.g. creating a project immediately triggers a "this is overdue" alarm; positive action lights a red badge)
- **Contradicts** an explicit promise of the app (e.g. "works on low-energy days" but the low-energy mode is a void)
- **Breaks a core flow** measurably (e.g. password reset email never sends; checkout fires no confirmation)
- **Loses user data silently** (e.g. unsaved-changes navigation away with no warning, where the data was non-trivial)
- **Causes a measurable trust event** (e.g. fake-progress bars, dishonest empty states, "12 people viewing this" social proof when there are zero)

If a stakeholder reads it and immediately says "yeah, we should fix that today," it's High. If they say "huh, interesting," it's Medium.

## Medium

The finding meets at least one of:

- **Causes confusion** that a thoughtful user can recover from with effort (e.g. jargon they can probably guess; nav badge with unclear meaning)
- **Causes mis-taps** at a non-trivial rate (e.g. destructive action adjacent to primary CTA; tap target slightly under 44pt)
- **Triggers anxiety or hesitation** disproportionate to the action (e.g. a friendly task wrapped in scary copy)
- **Creates vocabulary drift** the team has rationalised but a new user will trip over
- **Forces a learnable workaround** (e.g. user discovers they have to scroll down past the FAB to read the form)
- **Wastes premium screen real estate** (e.g. content vertically centered on the most important page)
- **Visual collisions** that aren't blocking but look unfinished (FAB overlapping a card, toast covering a button)

Most findings will be Medium. That's correct — Medium is where the actual product work lives.

## Low

The finding is real but cosmetic, easy to fix, and unlikely to cost a user the flow:

- Typos, microcopy nits
- Small alignment or spacing issues
- Optional CTAs that could be slightly more visible
- Polish on first-time states that returning users won't see often
- Empty space that's not ugly, just inefficient

Low findings still go in the table — they're free wins. But they should not dominate the top of the executive summary.

---

## Severity anti-patterns

Resist these tempting but wrong upgrades / downgrades:

- **"It's broken but rarely hit" → Medium.** No. If it's broken, it's High. Frequency is for the triage meeting, not the audit.
- **"It works as designed" → drop it.** No. "As designed" means the design is what's broken. Log it.
- **"Everyone gets used to it" → Low.** No. The audit is a *first-time user lens*; learned tolerance is not the test.
- **"The fix is hard" → downgrade.** Severity describes the user experience, not the engineering cost. The team weighs cost during triage.
- **"It's just one screen" → Low.** No. A core flow is a core flow even if it lives on one page.
- **"It's a known issue" → drop it.** No. Known issues need to stay surfaced; otherwise the team forgets the user is still hitting them.

---

## When in doubt

Pick the higher severity and add a one-line caveat in the "Why it's painful" cell. The reader can always downgrade in triage; they can't upgrade something they never saw.

The cost of one false-positive High in a 60-row table is a 30-second triage conversation. The cost of one missed Medium that should have been High is a feature that ships broken. The expected value points clearly at being honest, even slightly noisy.
