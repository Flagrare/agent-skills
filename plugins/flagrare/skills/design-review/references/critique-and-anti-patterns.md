# The critique process, and the anti-patterns to hunt

## The evaluation process, diagnose before you prescribe

A senior critique is *prioritized* and *tied to the screen's job*, three high-leverage moves beat
twenty equal-weight nitpicks.

1. **Name the ONE job of the screen** in a sentence. If you can't, the screen has no chance of
   expressing it. Then rank the content/actions by what the user needs first, second, third.
2. **The eye-landing / squint test.** Blur the screen; note what you see first, second, third. Check
   that path against the priority order. The most common senior finding: *visual* importance and
   *actual* importance are misaligned (a destructive action as loud as the primary; metadata
   outweighing the headline). If they don't match, **hierarchy is the #1 fix.**
3. **The subtraction question**, for every element ask *does this serve the one job?* Default to
   **remove → demote (to a caption) → keep-but-quiet**, in that order. Note: "minimal" is not license
   to strip *necessary* elements (labels, affordances); subtraction is goal-driven, not stylistic.
4. **Heuristic evaluation.** Hold the screen against **Nielsen's 10 heuristics** (see
   `principles.md`). Do **2-3 independent passes**, "any single evaluator misses issues." Cluster
   findings, then **prioritize by impact** (how much each hurts the job / the business goal), not a
   rigid score.
5. **Structure the output.** Lead with the **1-3 highest-leverage changes**, each stated as
   *observation → principle → recommendation* ("the two solid buttons compete → one primary only
   (Von Restorff) → make Cancel a ghost button"). Group the rest as "polish." A useful frame is
   **what works · what's hurting · what to try** (a.k.a. I-like / I-wish / What-if). Critique the
   design, never the designer.

## Why "packed/clunky" happens, name the cause before fixing

1. **Too many borders / dividers / shadows** competing, every box outlined.
2. **Everything the same visual weight**, no hierarchy, the eye has nowhere to rest.
3. **Inconsistent / arbitrary spacing**, no rhythm; gaps feel random.
4. **Too many columns / too much on one row**, horizontal overload.
5. **Heavy chips, badges, pills in dense rows**, loud decoration in an already busy table.
6. **Decoration over content**, gradients/icons/color where plain text communicates faster.

### The de-cluttering fixes (highest-leverage first)
- **Replace borders with spacing or a subtle background tint.** Group by whitespace (proximity); if
  separation is truly needed, a light shade or a single hairline beats a full border. Reducing
  competing lines is often the single biggest "de-clunk."
- **Demote secondary info to captions**, push meta to smaller/lighter/secondary text so primary
  content reclaims the weight. Establish the 3 text levels.
- **Right-align numerics** so magnitudes line up down the column.
- **Fewer columns**, cut low-value ones or fold them into the primary cell / an expandable detail.
  Each column is attention tax; keep the 20% users actually scan.
- **Lighten the chips**, soft-background, low-saturation, or drop the chip for plain colored text so
  status doesn't scream over content. Cap the count (e.g. 2 + a `+N` overflow).
- **Impose one rhythm**, snap all gaps to the spacing scale; consistent row height/padding instantly
  reads as "designed."
- **De-emphasize the competing sections** rather than fighting to make the important thing louder.

Every fix raises signal-to-noise: clunky ≈ too many equal-weight signals, and the cure is almost
always *remove, demote, or quiet*, rarely *add*.

## Anti-patterns, immediate senior flags

| Anti-pattern | Why it's wrong |
|---|---|
| Centered long/body text | Ragged left edge; the eye hunts for each line's start. Center only ≤ 2-3 lines of display text. |
| Grey text on a colored background | Muddy, low-contrast, cheap. Use a tint of the background's hue, not neutral grey. |
| Everything bold / one weight everywhere | Destroys hierarchy, if all is emphasized, nothing is; the eye has no entry point. |
| No clear primary action (or two "primaries") | Von Restorff + Hick's Law: raises decision time, lowers conversion. |
| Inconsistent / arbitrary spacing | Off-scale gaps read as random; breaks rhythm. Snap to the scale. |
| Over-bordered / cramped tables | Every cell outlined + tight padding = max noise, min scannability. Space + hairlines. |
| Low contrast (fails 4.5:1) | Excludes low-vision users; fails in real lighting. A hard accessibility floor. |
| Tiny (< 14px) *and* low-contrast text | Compounds unreadability, the worst pairing. |
| Too many typefaces / weights / accent colors | Exceeds ~7±2 working memory; fractures identity. Cap ~2-3 weights, one accent. |
| Tight line-height on long text | Lines blur together; body needs ~1.5 leading. |
| Decoration over clarity | Gradients/icons/chips where plain text is faster = noise; lowers signal-to-noise. |
| "Minimal" that removed *necessary* elements | Minimalism must be task-supporting, not merely sparse; don't strip labels/affordances. |

## The runtime loop (skill's executable core, order matters)
1. Name the **ONE job** + the user's priority order.
2. **Squint test**, does what survives match the priority? If not, hierarchy is fix #1.
3. **Heuristic pass** (Nielsen's 10), 2-3 passes; cluster, prioritize by impact.
4. **Subtract**, remove/demote/quiet everything that doesn't serve the job.
5. **Fix the levers:** one primary action; 2-3 weights/colors; weight+color before size; de-emphasize competitors.
6. **Whitespace & rhythm**, snap all spacing to one scale; macro space between groups.
7. **Legibility gate**, ≥ 4.5:1 body contrast, ~16px body, ~50-75ch measure, ~1.5 line-height; kill grey-on-color.
8. **Alignment**, fewest strong edges; left-align text; right-align numerics; optically center icons.
9. **Tokens**, reuse/extend the system; no per-screen invention.
10. **Deliver a prioritized critique**, the 1-3 highest-leverage moves first, each tied to a principle.

Sources: NN/g (*How to Conduct a Heuristic Evaluation*, *10 Usability Heuristics*, *Aesthetic & Minimalist Design*, *Characteristics of Minimalism*); Laws of UX (Aesthetic-Usability, Von Restorff, Hick's, Miller's); W3C WCAG 2.2 SC 1.4.3; Refactoring UI; critique frames (Rose/Thorn/Bud, I-like/I-wish/What-if).
