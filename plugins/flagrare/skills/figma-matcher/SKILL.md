---
name: figma-matcher
description: Enforces pixel-perfect implementation of Figma designs by exhaustively extracting every visual property from Figma, spinning up Chrome DevTools to measure the current implementation, building a full comparison checklist, and fixing all discrepancies in a single pass. MUST be triggered whenever implementing UI from Figma, fixing styling to match Figma, or any time the user says "match Figma", "check against Figma", "compare to design", "the design doesn't match", "colors are wrong", "spacing is off", or references a Figma URL in a styling context. Also trigger when you just finished writing CSS/styling code that was informed by a Figma design. This skill is NON-OPTIONAL when Figma designs are involved in styling work.
---

# Figma Matcher

A rigid, checklist-driven process for verifying that implementation matches Figma designs exactly. No visual impressions. No "close enough." Every property gets extracted, compared numerically, and verified.

## Why This Exists

Without this process, you will:
- Pick component variants by name without checking their actual hex values
- Assume "gray" means the same gray
- Skip checking spacing, border-radius, font-weight, opacity
- Iterate 3-5 times with the user correcting you each time

This skill eliminates all of that by forcing exhaustive upfront extraction.

## HARD GATE

You are FORBIDDEN from calling `Edit` or `Write` on any `.scss`, `.css`, `.sass`, `.less`, or `.styled.*` file until you have:
1. Completed Steps 1-4 below
2. Output the full comparison table to the user
3. Received acknowledgment or no objection from the user

If you catch yourself about to edit a styling file without having shown the comparison table, STOP. Go back to Step 1.

## The Process

You MUST complete every step in order. Do not skip steps. Do not combine steps. Do not start writing CSS until Step 5.

### Step 1: Extract ALL Properties from Figma

Call `get_design_context` on every relevant node. Also call `get_screenshot` to capture the Figma rendering for later visual comparison.

For each visual element, extract into a structured checklist:

**Colors** (resolve ALL to hex + rgba):
- Background color (including gradients, overlays, composite backgrounds)
- Border color + opacity
- Text color
- Icon color/fill
- Button background (default, hover, active, disabled states)
- Shadow colors

**Typography:**
- Font family
- Font weight (numeric, not name)
- Font size (px)
- Line height (px or unitless)
- Letter spacing
- Text transform

**Spacing:**
- Padding (top, right, bottom, left)
- Margin (top, right, bottom, left)
- Gap between elements

**Layout:**
- Width (fixed, %, auto, fill)
- Height (fixed, auto, fit-content)
- Display (flex, grid, block)
- Flex direction, align-items, justify-content
- Border radius (each corner if different)

**Borders:**
- Border width
- Border style
- Border color + opacity

**Effects:**
- Box shadow (offset-x, offset-y, blur, spread, color)
- Opacity
- Backdrop filter

**Button/Interactive elements:**
- Full width vs auto width
- Text wrapping behavior (nowrap, normal)
- Min-width constraints

Write these into a numbered checklist. Each item is a row you will verify later.

### Step 2: Resolve SCSS/CSS Variables to Actual Values

For every color, spacing, or size token in your codebase that might be relevant:

1. `grep` the variables file (e.g., `_settings.colors.scss`) to find the actual hex value
2. Follow any aliases (e.g., `$color-ui50: $color-gray50` -> find `$color-gray50: #BDBDBD`)
3. Record the full chain: `$variable-name` -> `$alias` -> `#hexvalue` -> `rgba(r, g, b, a)`
4. Compare against Figma values from Step 1

If a variable doesn't match exactly, note it. You will need a custom override, not a "closest match."

Example:
```
Figma border: rgba(103, 103, 103, 0.5) = #676767 at 50% opacity
$color-ui50 = $color-gray50 = #BDBDBD  --> NOT a match (189 != 103)
$color-ui70 = $color-gray70 = #676767  --> EXACT MATCH
```

### Step 3: Measure Current Implementation via Chrome DevTools

1. Ensure the dev server is running. If not, start it.
2. Use Chrome DevTools MCP to navigate to the page showing the component.
3. Take a screenshot of the current implementation (for visual comparison with Figma screenshot from Step 1).
4. For EVERY element in your checklist from Step 1, run `evaluate_script` to get computed styles:

```javascript
const el = document.querySelector('.your-selector');
const styles = window.getComputedStyle(el);
JSON.stringify({
  backgroundColor: styles.backgroundColor,
  borderColor: styles.borderColor,
  borderWidth: styles.borderWidth,
  borderRadius: styles.borderRadius,
  padding: styles.padding,
  paddingTop: styles.paddingTop,
  paddingRight: styles.paddingRight,
  paddingBottom: styles.paddingBottom,
  paddingLeft: styles.paddingLeft,
  margin: styles.margin,
  color: styles.color,
  fontSize: styles.fontSize,
  fontWeight: styles.fontWeight,
  fontFamily: styles.fontFamily,
  lineHeight: styles.lineHeight,
  letterSpacing: styles.letterSpacing,
  gap: styles.gap,
  width: styles.width,
  height: styles.height,
  minWidth: styles.minWidth,
  maxWidth: styles.maxWidth,
  display: styles.display,
  flexDirection: styles.flexDirection,
  alignItems: styles.alignItems,
  justifyContent: styles.justifyContent,
  boxShadow: styles.boxShadow,
  opacity: styles.opacity,
  whiteSpace: styles.whiteSpace,
  textOverflow: styles.textOverflow,
  overflow: styles.overflow,
});
```

Do this for EVERY element in the checklist. Not just the ones you think might be wrong. Check children, containers, buttons, icons, text spans, everything.

### Step 4: Build the Comparison Table and Present It

Create a markdown table with columns:

| # | Element | Property | Figma Value | Current Value | Match? | Fix |
|---|---------|----------|-------------|---------------|--------|-----|
| 1 | Banner container | background-color | rgba(103,103,103,0.08) | rgba(189,189,189,0.08) | MISMATCH | Use $color-ui70 instead of $color-ui50 |
| 2 | Banner container | border-color | rgba(103,103,103,0.5) | rgba(189,189,189,0.8) | MISMATCH | transparentize($color-ui70, 0.5) |
| 3 | CTA button | background-color | rgba(103,103,103,0.15) | rgba(0,85,255,0.15) | MISMATCH | transparentize($color-ui70, 0.85) |

Fill in EVERY row from your checklist. Mark each as MATCH or MISMATCH.

For mismatches, specify:
- Which file to change
- Which selector/property
- The exact new value (using the project's variable system where possible)

**OUTPUT THIS TABLE TO THE USER.** Do not proceed until you have done so.

Also show side-by-side screenshots: Figma (from Step 1) and current implementation (from Step 3).

### Step 5: Implement All Fixes in a Single Pass

Only after the table is complete and shown to the user:
- Make ALL changes at once based on the Fix column
- Do not iterate one property at a time
- Do not make partial fixes

### Step 6: Set `/goal` and Verify Until Zero Discrepancies

Before beginning verification, invoke `/goal` with the following condition:

```
/goal For every row in the Figma comparison checklist: re-run evaluate_script via Chrome DevTools on the live page, rebuild the full comparison table, and confirm every row shows MATCH (tolerance: <=2 subpixel rounding in rgba channels). Then take a fresh screenshot and compare side-by-side with the Figma screenshot from Step 1 confirming zero visible differences in color, spacing, sizing, typography, borders, shadows, or layout. Not met until the rebuilt table has 0 MISMATCH rows AND the screenshot comparison shows 0 visual discrepancies.
```

This activates Claude Code's built-in goal loop: you keep working across turns until the condition is met. The `/goal` evaluator will prevent premature completion.

#### Each verification pass within the goal:

1. Reload the page in Chrome DevTools
2. Re-run the SAME `evaluate_script` queries from Step 3 for EVERY row in the checklist (not just previous mismatches)
3. Build a fresh comparison table from the new measurements
4. Take a new screenshot
5. Compare screenshot visually against Figma screenshot from Step 1
6. Count: `mismatches_css` = rows where Current != Figma; `mismatches_visual` = visible discrepancies in screenshot
7. IF `mismatches_css == 0` AND `mismatches_visual == 0`:
     - Show the final comparison table with ALL rows marked MATCH
     - Show final screenshot alongside Figma screenshot
     - State: "0 CSS mismatches, 0 visual discrepancies"
     - Goal is satisfied
8. ELSE:
     - Log all remaining discrepancies in an updated table
     - Fix them
     - Run another pass

#### The goal is NOT met until:

- You have re-measured every single CSS property (not just the ones you fixed)
- The fresh comparison table shows MATCH on every row
- A new screenshot has been taken and compared to Figma
- No visual discrepancies remain between the screenshots

"Should match now" does not satisfy the goal. "Looks correct" does not satisfy the goal. Only measured values and screenshots satisfy the goal.

## Rules

1. **Never pick a variant/token by name.** Always resolve to hex and compare numerically.
2. **Never say "close enough."** Either the rgba values match or they don't. A 1-2 unit rounding difference in subpixel rendering is acceptable. A different base color is not.
3. **Never start writing CSS/SCSS before completing Steps 1-4 and showing the table.**
4. **Never skip Chrome DevTools.** Even if you "know" what the computed style is. Measure, don't assume.
5. **Every property gets checked.** Not just the ones that look wrong.
6. **If an existing component variant doesn't match exactly,** add a className override with the correct values. Don't use the "closest" variant and hope nobody notices.
7. **If the dev server isn't running,** start it before Step 3. Do not skip Step 3.
8. **Screenshots are mandatory** at Step 1 (Figma), Step 3 (before), and Step 6 (after).
9. **Button widths and text wrapping** must be explicitly checked. If a button is full-width in Figma, verify it's full-width in implementation. If text shouldn't wrap, verify `white-space: nowrap`.

## When This Skill Applies

- Implementing any UI from a Figma design
- Fixing styling discrepancies reported by the user
- After writing CSS/SCSS that was informed by a Figma design
- Any time a Figma URL is mentioned in a styling context
- When the user says anything resembling "doesn't match the design"
- Proactively, after completing any styling work that references Figma

## Output Format

Always output:
1. The numbered checklist (Step 1)
2. The variable resolution table (Step 2)
3. The full comparison table (Step 4)
4. Screenshots: Figma vs Current vs After-fix
