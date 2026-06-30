# Easing, springs & timing

Easing is the single highest-leverage variable in an animation, it can make a mediocre
animation feel great and a great one feel cheap. Get this right before anything else.

## Easing decision tree

| The motion is… | Use | Why |
|---|---|---|
| Entering or exiting (modal appears, toast slides in, element fades out) | **ease-out** | Starts fast, settles slow → reads as an immediate, responsive reaction. A 200ms ease-out *feels* faster than 200ms ease-in because the user sees movement instantly. |
| Moving / morphing across the screen (a shared element, a sliding panel between two points) | **ease-in-out** | Natural acceleration then deceleration, like a car pulling away and braking. |
| A hover color/background change | plain **`ease`** | The one built-in curve that's fine for simple, in-place property changes. |
| Constant, looping, or progress motion (spinner, marquee, progress bar) | **linear** | The only correct use of linear, steady motion with no start/stop. |
| Anything spatial/physical/interruptible (drag, momentum, "alive" elements) | **a spring** | See springs below, they carry velocity through interruptions. |

**Never use `ease-in` for UI.** It delays the initial movement, the exact moment the user is
watching most closely, and makes the whole interface feel sluggish. (Josh frames the symmetric
view: `ease-in` is acceptable specifically for things *leaving* the screen, accelerating out of
bounds. When in doubt for normal UI, ease-out is the safe default.)

**Never use `linear` for spatial motion.** Almost nothing in the real world moves at constant
velocity; it reads as robotic.

## Concrete curves (built-in curves are too weak)

CSS's built-in `ease-out` etc. are usually not strong enough to feel intentional. Use custom
cubic-beziers:

```css
/* Strong ease-out, default for UI enter/exit (Emil) */
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
/* Strong ease-in-out, for on-screen movement */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
/* iOS-style drawer/sheet curve (from Ionic) */
--ease-ios: cubic-bezier(0.32, 0.72, 0, 1);
```

Don't hand-guess 4 bezier numbers, use a visual tool (easing.dev, easings.co, Easing Wizard,
easings.net) and feel it.

**Match the curve to the component's personality.** A dense productivity tool wants crisp,
near-linear-out curves; a playful/marketing surface can run slightly slower and softer for
elegance (sonner deliberately uses a gentler `ease` and a slightly longer duration to feel
cohesive and refined). Keep easing, duration, and visual design singing in one key.

## Duration

Keep UI animations **under 300ms.** A 180ms dropdown feels markedly more responsive than a
400ms one even though the difference is a fifth of a second.

| Element | Duration |
|---|---|
| Button press feedback | 100-160 ms |
| Tooltips, small popovers | 125-200 ms |
| Dropdowns, selects | 150-250 ms |
| Modals, drawers | 200-500 ms |
| Hover-in | 125-250 ms |
| Hover-out | ~400-450 ms (relaxed) |
| Marketing / explanatory / first-run | can be longer |

**Asymmetric timing** mirrors intent: respond fast to the user's action, return to rest more
leisurely. Hover-in quick, hover-out slow. Hold-to-delete: a 2s linear press while they hold,
but a 200ms ease-out snap-back on release. Exits are usually a bit faster than enters.

**500ms is the frustration threshold** for anything the user is waiting on.

## Springs

Springs have no fixed duration, they settle based on physical parameters, and their killer
feature is **interruptibility**: a spring keeps its current velocity when retargeted, so it
reverses smoothly mid-gesture. CSS keyframes and `@keyframes` restart from zero.

**Use a spring when:** dragging with momentum, an element that should feel "alive" (a Dynamic
Island-style morph), interruptible gestures, decorative cursor-tracking. **Don't** spring
color/opacity (use a CSS transition) or anything in a dense, all-business tool where no
animation is better.

Configs (Framer Motion / Motion):

```js
// Apple-style, easier to reason about; recommended default
{ type: "spring", duration: 0.5, bounce: 0.2 } // keep bounce 0.1-0.3, often 0

// Traditional physics
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }

// react-spring intuition:
// tension/stiffness = how snappy (the main "speed" dial)
// friction/damping = how much it kills bounce (higher = no wobble)
// mass = heft (higher = slower, more overshoot)
{ tension: 300, friction: 10 } // snappy, slight overshoot (e.g. a "boop")
{ mass: 1.75, tension: 200, friction: 12 } // organic, weightier motion
```

Most production springs are **not** bouncy, turn friction up. Bounce is a deliberate, rare,
playful choice, not a default; never bounce dense/professional UI.

Decorative cursor-tracking: wrap mouse-derived values in a spring (e.g. Motion's `useSpring`,
`{ stiffness: 100, damping: 10 }`) so they have momentum instead of snapping, "nothing in the
real world changes instantly."

## Native CSS springs via `linear()`

Cubic-beziers have only two control points and **cannot overshoot** the target, so they can't
bounce. The CSS `linear()` timing function draws straight segments between many points, and
those points can exceed 0-1 to overshoot like a real spring:

```css
/* ~25% overshoot then settle, a spring without JS */
transition-timing-function: linear(
 0, 1.25, 1, 0.9, 1.04, 0.99, 1.005, 0.996, 1.001, 0.999, 1
);
```

Generate these with a spring-to-`linear()` tool. Humans recognize physical motion intuitively,
which is why physics-derived curves read as natural while hand-tuned beziers often feel "off."

## Transitions vs. keyframes vs. WAAPI

- **CSS transitions**, react to state/hover/class changes; interruptible and retargetable.
 Default for dynamic UI (toasts, toggles, anything retriggered).
- **`@keyframes`**, self-running, multi-step, or looping sequences. Note: the timing function
 applies to *each segment* independently; use `animation-fill-mode: backwards` to avoid a
 pop-in during `animation-delay`; parametrize with CSS variables to reuse one keyframe set.
- **`@starting-style`**, JS-free enter animations (replaces the `useEffect`/`data-mounted`
 hack).
- **WAAPI** (`element.animate(...)`), when you need programmatic control *and* GPU/off-main-thread.
