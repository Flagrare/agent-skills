# FINDINGS.md: template

Copy this verbatim into `.ux-audit/FINDINGS.md` at the start of an audit. Fill the executive summary last (after the table is complete) so it can name actual themes.

```markdown
# [App name] UX Audit: YYYY-MM-DD

**Tester:** Claude (first-time user lens)
**Viewport:** [e.g. Mobile-first 390×844 (iPhone 14)]
**Method:** Chrome DevTools MCP, every reachable route, every visible affordance

## Executive Summary

**Total findings: NN** (X High, Y Medium, Z Low)

### Top highest-impact issues

1. **[Theme name]** ([finding IDs]), one sentence on what's broken and why it matters
2. **[Theme name]** ([finding IDs]), …
3. **[Theme name]** ([finding IDs]), …

### Cross-cutting themes

- **[Theme]**: …
- **[Theme]**: …

### Routes covered

- [x] `/path`, what was tested
- [x] `/other`, …

### Not tested (gaps)

- `/private-thing`, needed test credentials I didn't have
- Push notifications, requires real device
- …

---

## Findings table

| # | Severity | Location | Issue | Why it's painful | Recommended fix |
|---|----------|----------|-------|------------------|-----------------|
| L01 | Medium | `/path` | one-sentence issue | one-sentence consequence to a real user | one-sentence concrete fix |

```

## Notes on filling the table

**ID prefixes**: pick short prefixes per route family so findings are greppable later. Examples that worked on real audits:

- `L##` landing / marketing
- `R##` register, `A##` auth (login/forgot/reset)
- `ON##` onboarding
- `T##` today / dashboard
- `S##` settings, `P##` profile
- `E##` error states (404, /offline)
- `G##` global (FAB, nav, header)
- `CT##` named UI components that appear app-wide

Pick prefixes once and stick to them. Mixed prefixes (`fleet01`, `F1`, `f-2`) make the file unreadable.

**Severity column**: see `severity-rubric.md`. Three values: `High`, `Medium`, `Low`. Don't invent `Critical` or `Trivial`, it dilutes the rubric.

**Location column**: be precise. `/fleet` is fine, `/fleet/[shipId] header` is better, `/fleet/[shipId] Routines kind picker` is best. The reader uses this to navigate to the screen.

**Issue column**: describe the symptom, not the cause. "Bottom nav badge `1` appears on a fresh project" beats "ListItem.notify() fires too early."

**Why it's painful column**: the user-facing consequence. If you can't articulate why it matters to a real human, downgrade or drop the finding.

**Recommended fix column**: one concrete sentence. Not "improve the UX", say what specifically to change. Bullet lists of three competing fixes belong in a follow-up doc, not here.

## Notes on the executive summary

Write the summary **after** the table is complete. Re-read the table and look for:

- **Frequency**: issues that recur across 5+ findings ARE the cross-cutting theme; name them
- **Severity clustering**: if 4 of 5 High findings live on the same screen, that screen is the headline
- **Promise contradiction**: issues where the app violates its own marketing promise. These belong at the top of "top issues" because they erode trust faster than any individual bug

Three to five top issues is the right size. Ten dilutes attention. One is suspicious, go back and look harder.
