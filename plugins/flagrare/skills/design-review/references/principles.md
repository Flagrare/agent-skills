# The design canon, named principles, and how they apply to UI

Cite these to ground a critique in something durable instead of taste. Each principle: the idea → its
concrete UI application.

## Dieter Rams, Ten Principles of Good Design
Maxim: **"Weniger, aber besser" (Less, but better)**, the brief is subtraction toward the essential.
1. **Innovative**, use genuine new capability to improve a workflow, not novelty for its own sake.
2. **Useful**, every widget, column, and field earns its place by serving the task; strip decorative chrome.
3. **Aesthetic**, spacing rhythm, type hierarchy, restrained color reduce fatigue and build trust in tools people use all day.
4. **Understandable**, "at best, it is self-explanatory": clear IA, labels, affordances, obvious primary action, real empty states.
5. **Unobtrusive**, the interface recedes so the user's content/data is the star.
6. **Honest**, no dark patterns, no fake progress, no inflated metrics; show real state. (Ties to Tufte's lie factor.)
7. **Long-lasting**, durable, convention-based patterns over trend-chasing; a system that survives redesigns.
8. **Thorough to the last detail**, "nothing must be arbitrary": aligned grids, pixel consistency, every edge case handled (loading / empty / error / overflow / zero / singular-plural).
9. **Environmentally friendly**, minimize "visual pollution" (screen clutter) and cognitive noise (and payload weight).
10. **As little design as possible**, ruthless reduction; remove every non-essential element until only what serves the task remains.

## Edward Tufte, data & information design
- **"Above all else show the data."** Data is the hero; chrome (borders, backgrounds, gradients, logos) must never outweigh the numbers.
- **Data-ink ratio**, maximize (data-ink ÷ total ink). Erase gridlines, heavy borders, cell shading, 3D. A card's drop shadow isn't data-ink; the number and its trend are.
- **Chartjunk**, kill moiré (pattern fills), dominant gridlines, and "ducks" (decoration overwhelming content, e.g. a KPI styled as a physical speedometer).
- **Small multiples**, a grid of identical mini-charts (per cohort/region) with shared axes beats one chart behind a filter dropdown.
- **Sparklines**, "word-sized graphics": an inline trend line beside a KPI or in each table row gives trend context without a separate chart.
- **Lie factor**, keep size-of-effect-shown ÷ size-in-data at ~1.0: never truncate a bar-chart axis; keep lengths/areas proportional.

## Gestalt principles, grouping & hierarchy (grouping strength: common region > proximity > similarity)
- **Proximity**, items close together read as one group. Tighten label-to-input; add space before the next pair; section a long form so it "appears less daunting." Whitespace groups even with identical styling.
- **Similarity**, shared visual traits read as related. Reserve one color for links; all primary CTAs share one color (same color = perceived equal importance).
- **Common region**, a shared boundary groups items (cards, bordered groups, zebra rows). Use "when whitespace alone proves insufficient", it can *overpower* proximity, so don't box everything.
- **Closure / Continuity**, the eye fills gaps and follows lines: negative-space icons; breadcrumbs, steppers, aligned rows read as a connected sequence.
- **Figure/Ground**, modals with a dimmed scrim; elevation/shadow makes dropdowns/toasts "pop" as figure and lessens cognitive load.
- **Prägnanz**, the eye prefers simple, regular, ordered forms; they resolve faster.

## Massimo Vignelli, the Canon
- **Discipline**, "Design without discipline is anarchy… Without discipline there is no good design, regardless of style." Enforce a constrained set of spacing/type/color tokens; freedom to use any value is anarchy.
- **Semantics / Syntactics / Pragmatics**, every choice maps to meaning; the same element looks/behaves the same everywhere; **if users don't understand it, elegance is void** (comprehension is pass/fail).
- **Limited type palette**, "a few basic ones, trash the rest." 1-2 families, a disciplined size/weight set. Font proliferation is "visual pollution."
- **Visual strength / Intellectual elegance**, one clear focal point, decisive contrast; the simplest structure that fully solves the problem; solutions feel inevitable, not busy.
- **Timelessness**, "will this look considered in 5 years, or is it chasing a trend?"
- **"The life of a designer is a life of fight against ugliness"**, the job is actively removing clutter, misalignment, and inconsistency.

## Josef Müller-Brockmann, grid systems
- The **grid is the first decision**; every element snaps to columns. Spacing/type derive from a system (8pt scale, modular type ratio), never eyeballed.
- **"Orderliness lends added credibility… and induces confidence."** Misaligned cards and inconsistent gutters literally reduce the perceived credibility of the data shown.
- The grid is an *aid*, not a guarantee, use it expressively (rhythm, hierarchy), not just mechanically filled.

## Don Norman, The Design of Everyday Things
- **Affordance vs Signifier**, the affordance is what's possible; the **signifier communicates where/that the action is**. A button that *looks* clickable (rounded + fill/shadow) is affordance + signifier; a flat borderless box reads as static text. Links need a consistent standout color.
- **Feedback**, press states, spinners/skeletons, save toasts, inline validation; no feedback = the user is unsure the action registered (the *gulf of evaluation*).
- **Mapping**, controls correspond to outcomes (slider left→right = low→high; layout mirrors what it controls).
- **Constraints**, prevent the wrong action (disable Submit until valid, block invalid dates) rather than punish it.
- **Discoverability**, surface actions; don't hide them behind unsignified gestures. "The two most important features of good design are discoverability and understanding."

## Jakob Nielsen, 10 usability heuristics (rules of thumb, not a checklist)
1. **Visibility of system status**, keep users informed with timely feedback.
2. **Match the real world**, users' language and conventions, not internal jargon.
3. **User control & freedom**, a clearly marked exit; Undo/Redo; obvious Cancel.
4. **Consistency & standards**, internal + platform conventions (Jakob's Law).
5. **Error prevention**, prevent problems before they happen (confirmations, good defaults, constraints).
6. **Recognition over recall**, make options visible; don't force memory (dropdowns, recents).
7. **Flexibility & efficiency**, accelerators for experts, hidden from novices.
8. **Aesthetic & minimalist design**, "every extra unit of information competes with the relevant units and diminishes their relative visibility." (Not a mandate for flat design.)
9. **Help users recognize/recover from errors**, plain-language errors, precise, with a recovery path.
10. **Help & documentation**, best if unneeded; when needed, searchable and task-focused.

## Cross-figure synthesis, the evaluation lenses these converge on
- **Every element earns its ink**, Rams (unobtrusive / as-little-design) ≡ Tufte (data-ink) ≡ Nielsen #8 ≡ Vignelli ("visual pollution"). Subtract until only the essential remains.
- **System over eyeballing**, Müller-Brockmann (grid) ≡ Vignelli (discipline): spacing/type/color from tokens; misalignment is a defect.
- **Hierarchy & grouping from whitespace**, Gestalt ≡ Tschichold (contrast) ≡ Vignelli (visual strength): one focal point, decisive steps, whitespace as an active tool.
- **Honesty**, Rams #6 ≡ Tufte (lie factor) ≡ Vignelli (semantics): encodings must be proportional and truthful.
- **Comprehension is pass/fail**, Vignelli (pragmatics) ≡ Norman (discoverability) ≡ Nielsen: if users don't understand it, elegance is void.

Sources: Vitsœ (Rams' Ten Principles); Tufte, *The Visual Display of Quantitative Information* / *Beautiful Evidence*; NN/g Gestalt series; *The Vignelli Canon* (PDF); Müller-Brockmann, *Grid Systems*; Norman, *The Design of Everyday Things* / jnd.org; NN/g *10 Usability Heuristics*.
