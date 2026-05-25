# Finding triggers — the heuristic checklist

This is the long version of the "what to flag" list in SKILL.md. Read once at the start of a long audit; skim whenever you feel the audit going thin.

Each trigger is phrased as a *symptom you should notice on the page*, not a principle. Principles ("respect Fitts's law") don't help in the moment; symptoms ("the destructive action is one tap-target away from the primary CTA") do.

The triggers are ordered roughly by how often they fire in practice. The first ten produce the bulk of findings on most audits.

---

## 1. Jargon the user hasn't earned

The app uses an internal term — entity name, branded feature, technical acronym — without ever defining it in context. Examples from real audits:

- `Set Your Light` as a button label (metaphor with no prior reference)
- `Calibrating · day 0 of 14` on a fresh item (technical state name + opaque countdown)
- `Hearthbeat` referenced in a banner before any explanation existed
- Section headers like `ALSO KEEPING ALIVE` that imply a sibling section that doesn't exist

The test is not "is the word in the dictionary." The test is "would a user who landed here from a Google search five seconds ago know what this means?"

## 2. Mystery glyphs

Icon-only controls in navigation, headers, or row actions, with no label and no obvious metaphor. Common offenders:

- Bottom nav with five icons and zero labels
- Header icons (pencil, anchor, ⋯) crowding the title row with no tooltip
- Row actions that are just an icon (trash, eye, arrow) with no caption

The fact that the icons are from a recognised library (Lucide, Heroicons) does not save them. Recognition ≠ identification.

## 3. Color-only signals

A red dot, green dot, orange highlight, or coloured outline carries meaning that no text reinforces. Color-blind users see nothing; sighted users guess wrong.

- Red dot beside an item with `aria-label="Inactive — needs attention"` but no visible text
- Green vs orange status pills with identical shapes and no label
- Form errors that change input border colour only, no inline message

## 4. Dead-end empty states

The user opens a page that says "Nothing here yet" and provides no path to create the first thing. Variants:

- Empty list with no "Add your first X" button
- "Add routines from your projects" with no link to projects
- Inbox/feed with no instructions for how items arrive

If the empty state is the most likely first impression of a page, it must include a CTA.

## 5. Premature alarms

The app fires a warning, badge, or notification against an entity that's too new to deserve one. The user is being punished for the action they just took.

- "This project has been quiet for weeks" toast on a project created seconds ago
- Red `Inactive` dot on a freshly-created item
- "Streak broken" banner on day 1
- "Overdue" status on an item with no due date set

Fix is almost always "introduce a grace period."

## 6. Choice paralysis

Three or more equally-weighted CTAs on one screen with no clear primary. The user has to read every button before acting.

- Two `Add project` buttons (top-right outline + center primary) on the same empty state
- A recommendation card with Check-in + Resume + Mark as win + How does this feel + Close the day all visible
- Onboarding steps with two siblings that both look like "next"

The fix is rarely "make all the buttons smaller." The fix is "pick one primary, demote the rest."

## 7. Tone mismatch

Affirming/poetic copy lives next to operational copy in the same visual frame. The register clashes.

- "Still here. That matters." headline directly above an `Add an action…` form input
- "You're set up ✨" affirmation card on the same page as a Sign Out button
- Microcopy that switches register mid-screen ("Your purpose ✨" then "Save changes")

The rule: affirmations belong on transitions and empty states, not adjacent to primary CTAs.

## 8. Vertical-center waste

Content is `justify-center` on a tall mobile viewport. The top 40% of the page is dark void; the user has to scroll for what should be above the fold.

- Hero pages where the logo and CTAs float in the middle with empty header
- Form pages where the title pushes inputs below the fold
- Empty states that center vertically and leave headers floating

The fix is almost always `justify-start` with comfortable top padding.

## 9. Truncated text

Strings get clipped because the container is too narrow or the placeholder is too long.

- Placeholder `What just pulled at your attention?` → renders `What just pulled at your attentior`
- Button labels that wrap awkwardly on iPhone SE width
- Table cells that ellipsize critical data

This always reads as "unfinished" to a real user, regardless of cause.

## 10. Tap-target violations

Interactive controls smaller than 44×44pt on mobile. Common offenders:

- Header back chevron rendered as a single character glyph
- Inline icon buttons in row actions
- Tab triggers in narrow tab strips
- "Cancel" text links sized like body text

Apple HIG and Material both put 44pt as the floor for the same reason — fingers aren't pixel-precise.

---

## 11. Modal on mobile

A Dialog component is used where a bottom Drawer would fit better. Symptoms:

- Centered modal on a phone with most of the viewport dark/dimmed
- Small input field cramped in the centered modal
- User has to reach the top of the screen to dismiss

Drawer-from-bottom matches the thumb's natural reach zone.

## 12. Silent saves

A destructive or important action completes with no toast, no banner, no inline confirmation. The user can't tell if it worked.

- "Save" on a settings page reloads silently
- Form submits, page state changes, no acknowledgement
- "Delete" succeeds with the item disappearing — but the user wasn't sure it was their tap or a glitch

The fix is a brief toast: "Saved ✓" / "Deleted — undo".

## 13. Vocabulary drift

The same concept is named differently across screens, or two different concepts share a name.

- Sidebar says "Projects", page header says "Threads", a different page says "Ships"
- "Catch a thought" FAB but "Impulses" nav entry for the same feature
- Two distinct entities both called "Activity"

Even the most fluent users will misnavigate at least once because of this. The fix is a glossary + a copy lint.

## 14. Layout collisions

UI layers overlap because the absolutely-positioned thing didn't reserve scroll padding.

- FAB overlapping the last list item / form button on every scroll-end
- Toast overlapping a modal
- Sticky header covering a focused input on keyboard open

The fix is page-level `pb-24` (or whatever the FAB height is) on every scrollable area.

## 15. Form gotchas

Form interactions that feel sloppy even when "working":

- Browser-native HTML5 validation tooltips on dark themes (white bubble pops out of nowhere, covers buttons)
- No show-password toggle
- No password confirmation field
- Required fields with no asterisk or label hint
- Inline error appears below the input but the input has no error style itself
- Enter key on the last field doesn't submit

## 16. IA gaps

Major features are reachable only via deep-links — not surfaced in primary navigation. A new user will never find them.

- The app's central concept (e.g. "The Light") has no nav entry
- A reports/analytics page is reachable only via a small text link on a settings sub-page
- An entire feature surface sits behind 3+ taps from the home screen

The audit's job is to *surface* this, not to redesign IA. Recommend "promote to nav" or "surface in dashboard" and move on.

## 17. Validation / state contradictions

The app fires a follow-up notification or state that contradicts what the user just did:

- "Was that the win?" prompt asking about a session that happened 5 seconds ago
- "Don't forget to..." reminder for something the user just completed
- Empty state shown after a successful create (because the list query stale-cached)
- Toast that names a different entity than the user just touched

These are bugs as much as UX issues — log them both ways.

## 18. Onboarding crimes

Onboarding-specific patterns that bite first-time users hardest:

- Multi-step flow with no progress indicator
- Bottom nav / global FAB visible during onboarding (and tapping it bounces them back)
- Final "you're set up!" screen that immediately drops the user into a void
- "Skip for now" link that loses every previous answer
- Required fields with no validation feedback until submit

---

## What NOT to flag

Some things look like findings but aren't. Resist:

- **"I would have designed it differently"** — design preference is not a UX defect. Stick to user-impact.
- **"It's not how Stripe does it"** — apps are allowed to be different. Only flag if the difference creates user-side friction.
- **Minor brand/style nits on internal-only screens** — admin tools have looser polish bars; respect the context.
- **Things you'd need a contract change to fix** — e.g. "the entire data model should be different." Out of scope for a UX audit. Recommend a separate architectural conversation.
- **Performance issues that aren't visible to the user** — load times, bundle size, etc. belong in a different audit.

The audit's value comes from being trustworthy. Every clear false-positive in the table erodes that trust, even if the rest of the findings are gold.
