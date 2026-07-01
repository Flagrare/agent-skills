# Tactical playbook, how to actually make it look designed

From **Refactoring UI** (Adam Wathan & Steve Schoger). Each: tactic → concrete rule → why.

## Hierarchy (the highest-leverage lever)
- **Encode importance with size + weight + color, not size alone.** Size is loudest and most abused; weight and color add contrast *at a fixed size*, so secondary text needn't shrink to illegible or grow to competing.
- **Assign every element a tier (primary/secondary/tertiary) before styling.** Emphasis is relative and finite, if everything is bold, nothing is.
- **~2-3 text colors per surface** (dark primary, soft-grey secondary, lighter tertiary) and **≤ ~2 weights**. A single black flattens hierarchy; color de-emphasis reads instantly.
- **Never go below weight 400 in UI.** Light weights (100-300) only survive at large display sizes; at 14-16px they're illegibly thin.
- **Emphasize by de-emphasizing.** If the hero won't pop, mute its neighbors instead of amplifying it, contrast is relative, and it keeps the whole screen calm.
- **Buttons by hierarchy, not semantics.** Primary = solid high-contrast fill; secondary = outline/soft-fill/low-contrast; tertiary = looks like a link. Two solid buttons compete; recede the secondary. De-emphasize destructive actions until the confirming moment.
- **Fold labels into values.** "12 left in stock", "$19/mo", not "Stock: 12". The label is usually inferable and steals emphasis from the value.
- **Visual hierarchy ≠ DOM hierarchy.** A page's `<h1>` or a field label need not be the most prominent thing; the *content* is often the star. Don't size by heading level.
- **On colored backgrounds, don't de-emphasize with grey**, use a shade of the *same hue* (lower opacity / lighter tint). Grey-on-color goes muddy.

## Spacing & whitespace
- **Start with too much whitespace, then remove.** Dense is developers' default failure; it's easier to tighten than to loosen.
- **Use a constrained spacing scale, never arbitrary values.** Base 16px; grow non-linearly: `4 8 12 16 24 32 48 64 96 128 192 256 384 512`.
- **≥ ~25% gap between adjacent scale steps**, closer than that and the difference is invisible, making choices ambiguous.
- **Whitespace implies grouping** (proximity): more space *around* a group than *within* it. A label sits closer to its own input than to the field above.
- **Density is a deliberate choice**, airy for marketing/consumer, tighter for data-dense tools. Decide per context.
- **Don't stretch content to 100% just because the space exists**, constrain widths; balance in columns.

## Typography
- **A fixed modular type scale; limit the sizes.** e.g. `12 14 16 18 20 24 30 36 48 60 72`. Use px/rem, avoid `em` (compounds when nested). Hand-pick, strict ratios cluster unusable sizes at the small end.
- **Measure: 45-75 characters per line (~66 ideal).** Set `max-width` in `em` on text blocks. The top readability lever.
- **Line-height scales *with* size and *inversely* with measure.** Body ~1.5-2; large headings ~1-1.25; wider columns → more leading.
- **Limit weights and families** (a couple of weights, 1-2 families).
- **Don't center long-form text**, only runs of ≤ 2-3 lines. A ragged left edge kills the return sweep.
- **Align mixed-size inline text by baseline, not center** ("$19" + "/mo").
- **Letter-spacing, directional & sparing:** tighten large display slightly, add tracking to ALL-CAPS labels, leave body alone.
- Pick a good default face / quality system stack; restyle ugly UA defaults (links, bullets, quotes).

## Color
- **Define color in HSL**, maps to intuition ("same color, darker" = one number); hex hides relationships.
- **Build a full palette, not 5 hex codes.** Per family ~8-10 shades: greys (8-10), 1-2 primaries (×5-10), semantic accents (red/yellow/green ×5-10). You need borders, hovers, muted text, backgrounds, disabled states.
- **"Grey isn't grey", give greys a temperature** (a touch of blue = cool, yellow/orange = warm), kept consistent. Use a very dark grey, never pure `#000`.
- **Increase saturation toward the lightness extremes** so light/dark shades don't wash out to grey.
- **Don't rely on color alone**, pair with icon/text/shape (error = red *and* icon *and* label).
- **Accents used sparingly**, reserve the most saturated color for the few things that must draw the eye. Overused accent destroys its own emphasis.

## Depth & elevation
- **Shadows on a ~5-level elevation scale**, small = buttons/cards, medium = dropdowns, large/diffuse = modals.
- **Light comes from above**, lighter top edge, shadow below; inset/pressed inverts it.
- **Layer two shadows**, a tight darker ambient + a larger softer cast, for real depth. A single shadow looks flat.
- **Shadow + a hairline border** crisps the edge on light backgrounds.
- **Flat-design depth:** color + a short hard offset (lighter = closer), or **overlap** elements to imply layering.

## Data & tables
- **Right-align numbers; use tabular (lining) figures**, the eye compares magnitudes down a column; proportional figures break the alignment.
- **Emphasize the one primary column (name/title); mute IDs, dates, meta.** Equal-weight cells are unreadable.
- **Give rows vertical room and generous cell padding**, tight rows read as a spreadsheet dump.
- **Kill heavy per-cell borders**, prefer whitespace, zebra striping, or a single hairline row divider.
- **Combine related data into one cell** (avatar + name + email; "12 in stock") to cut columns and horizontal scanning.
- **Status via muted, consistent badges**, categorical scanning without shouting.

## Forms
- **Top-aligned labels, close to their input** (closer than to the field above). Fastest to scan; unambiguous pairing.
- **Real input affordance**, a border or subtle inset shadow so it looks fillable, a visible focus state, adequate height/padding.
- **Don't overuse borders/lines**, group with whitespace or a subtle background tint first; every border is visual weight.
- **Brand the controls** (checkboxes/radios/selects) rather than shipping raw OS defaults.
- **Strong emphasis only on the submit/primary action.**

## Empty states & pro polish
- **Design empty states**, an icon/illustration, one line of explanation, one clear CTA. It's often the first thing a new user sees; a blank page looks broken.
- **Sweat the details**, custom bullets → icons; styled links; an accent border on the top of a card or side of an alert; rounded, controlled images (`background-size: cover` + inner shadow). The accumulation reads as craft.
- **Don't up-scale icons 3-4×** or down-scale screenshots/favicons, use a size-appropriate asset.

## Process tricks
- **The squint test.** Blur the screen; whatever still dominates is what the user sees first. If the hero vanishes and a stray chip survives, hierarchy is inverted.
- **Work in grayscale first**, forces hierarchy to come from spacing/size/contrast, not color as a crutch.
- **Design with real, representative content**, real-length names, huge numbers, empty and overflow cases, not lorem ipsum.
- **Limit choices up front**, predefine the spacing, type, color, shadow, and radius scales *before* screens. Every value you then pick is already "correct."

## Canonical numbers to bake in
| Domain | Default |
|---|---|
| Spacing scale | 16px base; `4 8 12 16 24 32 48 64 96 128…`; ≥25% between steps |
| Type scale | fixed set `12 14 16 18 20 24 30 36 48 60 72`; px/rem not em |
| Measure | 45-75 chars (~66 ideal) |
| Line-height | body ~1.5-2; headings ~1-1.25; ↑ with measure |
| Font weight | body 400-500, emphasis 600-700; never < 400 |
| Text colors | ~2-3 per surface |
| Contrast (WCAG 1.4.3) | body ≥ 4.5:1; large (≥24px, or ≥18.7px bold) ≥ 3:1, hard floor |
| Palette | HSL; greys 8-10, primaries ×5-10, accents ×5-10; no pure black |
| Shadows | ~5-level scale; light from above; two layered; + hairline |
| Tables | right-align + tabular numbers; primary column emphasized; rows breathe; no cell borders |
| Gradients | two hues within ~30° |

Sources: refactoringui.com; Wathan & Schoger, "7 Practical Tips for Cheating at Design"; W3C WCAG 2.2 SC 1.4.3.
