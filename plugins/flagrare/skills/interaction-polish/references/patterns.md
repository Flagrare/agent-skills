# Per-component recipes

How to make each common interaction feel good. Every recipe assumes the guardrails in
SKILL.md (frequency-gate, transform/opacity only, reduced-motion path). Numbers are starting
points, tune by feel, then review the next day in slow motion.

## Button / pressable
The cheapest, highest-impact polish. Acknowledge the press:
```css
.btn { transition: transform 150ms cubic-bezier(0.23, 1, 0.32, 1); }
.btn:active { transform: scale(0.97); } /* 0.95-0.98; "the UI is listening" */
```
Note `scale()` scales children too, usually what you want. Add a subtle shadow drop on press
for extra tactility. Don't animate primary nav buttons the user hammers all day.

## Toggle / switch
Thumb slides ease-out with a slight overshoot; track color cross-fades; tiny thumb scale-pop on
settle (~120-150ms). **Always optimistic**, flip immediately, never gate the visual on a
network request; reconcile if it fails.

## Like / favorite
Icon **pop** (scale 1 → 1.3 → 1 via spring), color fill, optional one-shot particle/confetti
burst. Fire instantly (optimistic; revert only on failure, like Twitter's heart). Particles are
a *delight moment*, the hero action, not every icon on the page.

## Modal / dialog
Scale + fade, ideally from the trigger's position so cause→effect reads:
```css
/* enter */ transform: scale(0.95); opacity: 0; → scale(1); opacity: 1; /* 200ms ease-out */
```
Backdrop fades in parallel. Reverse on close (scale down + fade), slightly faster. Modals stay
`transform-origin: center` (they aren't anchored to a trigger like a popover is).

## Popover / dropdown / tooltip
**Origin-aware** scaling, scale from the trigger, not the center:
```css
transform-origin: var(--radix-popover-content-transform-origin); /* or Base UI's --transform-origin */
```
Tooltips: delay the *first* one (prevents accidental activation), but once one is open, adjacent
ones open instantly (`transition-duration: 0ms`), feels faster without losing the safety delay.

## Drawer / bottom sheet (the vaul feel)
This is direct-manipulation game feel, the finger tracking *is* the polish.
- Hide off-screen with `translateY(100%)` (percentage = relative to its own size, works at any
 height).
- During drag, track the pointer **1:1**; set `element.style.transform` directly (don't animate
 an inherited CSS var on a parent, it recalcs all children).
- **Dismiss on velocity, not just distance:** `velocity = |dragDistance| / elapsedTime`; if
 `velocity > ~0.11` OR past a distance threshold, dismiss, a quick flick should be enough.
- **Damp at boundaries** (the more they overscroll, the less it moves) instead of a hard wall.
- **Pointer capture** so the drag survives the pointer leaving the element; ignore extra touch
 points after a drag starts (else it jumps to the new finger).
- Use a spring on release so an interrupted drag reverses smoothly. iOS curve: `cubic-bezier(0.32, 0.72, 0, 1)`.
- Backdrop opacity tracks drawer position.

## Toast / notification (the sonner feel)
Slide-in + fade (`translateY(16px)` → 0, ease-out, ~200ms). **Stack** multiple with the front
toast full and others scaled/offset behind it; use **CSS transitions (not keyframes)** so a
newly added toast retargets the stack smoothly instead of restarting. Auto-dismiss reverses the
enter. Invisible details that make it premium: pause the dismiss timer when the tab is hidden;
fill the gaps between stacked toasts with pseudo-elements so hover keeps the stack open.

## Tabs / segmented control
A shared indicator (underline or pill) that **slides** between tabs (animate via `transform`,
spring or ~200ms ease-out); content cross-fades. The sliding indicator is the signature juice.

## Accordion
Animate height (or a `grid-template-rows: 0fr→1fr` / clip trick for perf), chevron rotates 180°,
content fades in slightly delayed. ~200-250ms. Height animation triggers layout, prefer the
clip/grid trick or transform where you can.

## List enter/exit & drag-reorder
- Enter/exit: combine `opacity` + `height` (or transform), trial and error, no formula; adjust
 until it feels right. **Stagger** entrances 30-80ms between items; never block interaction
 during a stagger.
- Drag-reorder: lifted item gets `scale(1.03)` + elevated shadow + slight opacity; siblings
 shift with a spring to open the gap (FLIP: animate layout changes via `transform`); drop
 settles ease-out.

## Hover / focus (desktop pointer only)
Subtle lift: `transform: translateY(-2px to -4px)` + a stronger shadow tier, ~150ms ease-out.
**Separate the trigger from the thing that moves** to avoid the "Doom flicker", if the hovered
element itself translates, it can slide out from under the cursor and re-trigger endlessly. Keep
the outer element stationary (it owns `:hover`); move only a child:
```css
.card { /* stationary, owns :hover */ }
.card .surface { transition: transform 150ms; }
.card:hover .surface { transform: translateY(-4px); }
```
Gate behind `@media (hover: hover) and (pointer: fine)` so taps on touch devices don't fire
false hovers. Always pair with a visible `:focus-visible` state.

## The "boop" (Josh's signature delight)
A momentary, **self-resetting** hover transform (rotate/scale/translate) that springs back, 
versus a sticky hover state, which feels robotic. `onMouseEnter` sets `booped = true`; a
`setTimeout` flips it back after the spring settles; combine all transforms into one string;
drive with a snappy spring (`{ tension: 300, friction: 10 }`). A `useBoop([style, trigger])`
hook decouples the trigger from the animated element (hovering a button can boop the icon
inside it) and returns no animation under reduced-motion. **Rare by design**, boop a few
accents, never everything.

## Friendly shadows (Josh)
Flat black shadows look cheap. Make them real:
- **One light source** for the whole page (convention: top-left; vertical offset ≈ 2× horizontal).
- **Layer several `box-shadow`s** with increasing offset+blur, each low-opacity, instead of one.
- **Tint, never pure black**, match the surface hue, drop saturation/lightness, via a
 `--shadow-color` var that inherits per background.
```css
box-shadow:
 1px 2px 2px hsl(220deg 60% 50% / 0.333),
 2px 4px 4px hsl(220deg 60% 50% / 0.333),
 3px 6px 6px hsl(220deg 60% 50% / 0.333);
```
- **Elevation = bigger offset + bigger blur + lower opacity**, as a shared small/medium/large
 system. On hover, jump to a higher tier to read as lifting toward the user. (Animated
 box-shadow is paint-heavy, if perf matters, cross-fade a pre-rendered shadow layer instead.)

## Loading
Match the indicator to the wait:
- **Optimistic UI** (no spinner) for low-risk actions (like/toggle/save), show success
 immediately, reconcile on failure.
- **Skeleton screens** for content (perceived ~30% faster than spinners); mirror the final
 layout.
- **Spinners** only for short, genuinely indeterminate waits; **progress bars** for measurable
 ones. A fast-spinning spinner makes the app feel quicker even at equal load time.
- Never a full-page blocking spinner for something you could do optimistically.

## Scroll-triggered reveal
Fade + small `translateY` (≤16px) as the element enters the viewport, ease-out, **once**. Use
`IntersectionObserver`, never a scroll handler. Keep travel small and never re-trigger on every
scroll tick. Drop the movement entirely under reduced-motion (keep the fade).

## Page transition
Cross-fade or a shared-element morph (a hero image persisting across routes). ≤300ms, this is
on the critical path, so it must stay snappy.
