# Accessibility, performance & anti-patterns

These are not optional polish, they are what makes motion *safe* and *smooth*. Ship them by
default, from the first version.

## prefers-reduced-motion

Motion can cause real harm, dizziness, nausea, migraine, vestibular distress (up to ~35% of
adults 40+ have experienced vestibular dysfunction; also relevant for ADHD, autism, epilepsy).
`prefers-reduced-motion: reduce` is a defensive default, not a niche toggle.

**The rule: reduce/replace MOTION, never delete the message.** A modal that flies up becomes a
modal that *fades* in, it must not become a modal that appears with no indication at all. Every
state change must still be communicated.

**Drop or replace** (these change perceived size/shape/position):
- Large translations, sliding panels, big cross-screen movement
- Parallax, scroll-jacking
- Spin / rotation, 3D/depth
- Large scale/zoom
- Auto-playing carousels, looping motion, flashing (seizure risk)

**Keep** (WCAG explicitly excludes these, they don't move/resize):
- Opacity / fade
- Color changes
- Blur
- *Small* movements (a few px)
- Shortened durations as a fallback

**Implement it as opt-IN to motion** so motion is additive and you can't forget to remove it:
```css
@media (prefers-reduced-motion: no-preference) {
 .panel { transition: transform 300ms cubic-bezier(0.23, 1, 0.32, 1); }
}
/* the panel still fades/changes color for everyone; only the transform is gated */
```
React: a `usePrefersReducedMotion()` hook (query `(prefers-reduced-motion: no-preference)`,
default to "reduced" on the server to avoid SSR flashes), wired to the spring's `immediate` prop
or returning no transform.

**Avoid the nuke-everything reset.** A blanket `*, *::before, *::after { animation-duration:
0.01ms !important; transition-duration: 0.01ms !important; }` kills safe fades *and* can
paradoxically *speed up* JS/spring animations (making them more dizzying). If you use a global
fallback, keep opacity/color cross-fades as the substitute rather than zeroing everything.

**Test it:** Chrome DevTools → Command Palette → "Emulate CSS prefers-reduced-motion: reduce."

## Performance, compositor-only

The render pipeline is **Layout → Paint → Composite**. Composite is cheapest (GPU, off the main
thread). The whole game is staying in Composite.

- **Animate only `transform` and `opacity`.** They skip layout and paint and run on the GPU.
- **Never animate geometry**, `width`, `height`, `top`, `left`, `margin`, `padding` force a
 layout/reflow *every frame* and can cascade to siblings. This is the #1 source of jank. Use
 `translate()` / `scale()` instead. (For a height animation that must happen, prefer a
 `grid-template-rows: 0fr → 1fr` or clip-path trick over animating `height`.)
- **Avoid paint-heavy animation**, animated `box-shadow`, `filter`, blur, large background
 repaints. Fake a shadow lift by cross-fading a pre-rendered shadow layer (an opacity-animated
 pseudo-element) instead of animating the shadow itself. Keep blur values modest (<20px;
 expensive in Safari).
- **`will-change` is a scalpel, not a default.** It promotes an element to its own GPU layer, 
 great just before a known animation, but every layer costs memory, and broadly applying it
 *hurts* performance. Add it right before animating (ideally via JS) and remove it after; never
 ship it permanently on many elements.
- **Name exact properties, never `transition: all`.** `all` animates things you didn't intend
 (including properties added later) and quietly re-introduces layout animations.
- **In Framer Motion, the `x`/`y`/`scale` shorthands are NOT hardware-accelerated** (they run on
 rAF/main thread). Use a full `transform: "translateX(100px)"` string for GPU. And remember:
 a hardware-accelerated CSS animation stays smooth no matter how busy the main thread is, 
 which is why CSS beats JS for predetermined motion. (Real case: a dashboard tab animation
 dropped frames on load via JS shared-layout; moving it to CSS, off the main thread, fixed it.)
- **Keep scroll & gesture paths sacred:** `IntersectionObserver` (not scroll handlers) for
 reveals, keep finger-tracking 1:1, no long durations on scroll-linked motion. Target 60fps
 (~16.7ms/frame); verify in DevTools (FPS meter, Paint Flashing, Performance panel).

## Anti-patterns (when NOT to add juice)

The most important section. Each of these makes UX *worse*:

1. **Motion that delays or blocks the user.** If interaction pauses while an animation plays,
 the app is now slower. Keep anything blocking <300ms; ideally never block, let users tap
 through.
2. **Durations too long → sluggish.** Past ~400-500ms, UI motion reads as lag. A tenth of a
 second too long is felt.
3. **Non-interruptible / trapping animations.** Any celebration or transition must be
 dismissible/skippable. Never lock input until it finishes.
4. **Animating everything.** When all elements move, nothing signals importance; motion loses
 its meaning and adds cognitive load. Motion marks *meaningful* state change.
5. **Decoration over feedback.** Flourish that doesn't answer "did it register / what changed /
 where did it go" is gratuitous. Feedback first.
6. **Gratuitous spinners.** Inventing a wait for something you could do optimistically or
 skeleton-load. Full-page blocking spinners actively hurt perceived performance.
7. **Ambient / auto-triggered motion** (looping, parallax, autoplay), raises cognitive load,
 creates a11y barriers, rarely earns its cost.
8. **Layout-thrashing animation.** Looks fine, drops frames, the jank cancels the polish.
9. **Linear easing & instant snaps.** Opposite failures of craft: linear feels robotic, a
 zero-transition state change feels dead.

**Default heuristic:** add the smallest feedback that confirms the action within ~100ms; add
flourish only at genuine moments (success, completion, first-time delight); and ship the
reduced-motion + compositor-only version from day one. When in doubt in a dense, professional,
speed-first tool, less motion, or none, is the right answer.
