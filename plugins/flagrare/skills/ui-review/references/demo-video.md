# Recording a demo or before/after as MP4

A demo of an interaction fix has to show timing: how fast the press responds, how the dialog enters, whether the spinner flashes. Screenshots stitched into a GIF throw the timing away and read as a slideshow. So the video is a real-time recording of the browser, with a cursor the viewer can follow.

## What you need

- **Playwright from the project.** Resolve `@playwright/test` (or `playwright`) from the project's `node_modules`, the same way `/flagrare:visual-diff-branches` does in its `scripts/lib.mjs`: run the script with the project root as the working directory. Do not install Playwright into the skill folder.
- **ffmpeg** for the MP4 conversion. Check with `command -v ffmpeg` before promising an MP4. Without it, ship the `.webm` Playwright wrote and say so in the hand-off.
- **A saved login**, when the target is behind auth: a Playwright `storageState` file (most projects with Playwright e2e already write one in a setup project).

Run the script with the sandbox disabled when the agent sandbox blocks `localhost`. If `launch()` fails with "Executable doesn't exist", the project's Playwright version has no downloaded browser: launch the installed Chrome with `chromium.launch({ channel: 'chrome' })` rather than downloading one.

## The script

Keep it in the scratchpad or `.ui-review/`, out of git. It replays one path through the interaction, the same path for before and after.

```js
// .ui-review/record.mjs  usage: node .ui-review/record.mjs before|after
import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';

const { chromium } = createRequire(path.join(process.cwd(), 'package.json'))('@playwright/test');
const label = process.argv[2] ?? 'demo';
const size = { width: 1280, height: 800 };
const out = path.resolve('.ui-review/video', label);

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: size,
  recordVideo: { dir: out, size },
  // storageState: 'playwright/.auth/user.json',
});

// Playwright videos have no cursor. Draw one that follows the real mouse events.
await context.addInitScript(() => {
  const draw = () => {
    const dot = document.createElement('div');
    Object.assign(dot.style, {
      position: 'fixed', left: '-40px', top: '-40px', width: '20px', height: '20px',
      margin: '-10px 0 0 -10px', borderRadius: '50%', pointerEvents: 'none',
      background: 'rgba(0,0,0,0.35)', border: '2px solid #fff',
      boxShadow: '0 0 0 1px rgba(0,0,0,0.4)', zIndex: '2147483647',
      transition: 'transform 90ms ease-out',
    });
    document.documentElement.appendChild(dot);
    addEventListener('mousemove', (e) => { dot.style.left = `${e.clientX}px`; dot.style.top = `${e.clientY}px`; }, true);
    addEventListener('mousedown', () => { dot.style.transform = 'scale(0.7)'; }, true);
    addEventListener('mouseup', () => { dot.style.transform = ''; }, true);
  };
  if (document.documentElement) draw(); else addEventListener('DOMContentLoaded', draw);
});

const page = await context.newPage();

// Move like a person: a glide to the target, a short pause, then a real press.
async function press(locator) {
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 30 });
  await page.waitForTimeout(300);
  await page.mouse.down();
  await page.waitForTimeout(80);
  await page.mouse.up();
}

await page.goto('http://localhost:3000/checkout');
await page.waitForLoadState('networkidle');
await page.waitForTimeout(600);

await press(page.getByRole('button', { name: 'Pay now' }));
await page.waitForTimeout(1500); // let the result settle on camera

const video = page.video();
await context.close(); // the video file is written on close
await browser.close();
fs.renameSync(await video.path(), path.join(out, `${label}.webm`));
console.log(path.join(out, `${label}.webm`));
```

Rules for the replay:

- **Real input only.** `page.mouse.move` with `steps`, `mouse.down` and `mouse.up`, `keyboard.type` with a `delay`. `locator.click()` teleports the pointer and the cursor jumps.
- **Pauses are for the viewer**, a few hundred milliseconds before each press and a second or so after each result. Never speed the recording up and never cut frames out.
- **Same script, same data, both sides.** The before and after must differ only by the fix. Reset any state the path creates (a draft, an added item) before the second run.
- **Show the reduced-motion version too** when a motion fix ships: `await page.emulateMedia({ reducedMotion: 'reduce' })` before `goto`, recorded as its own clip.

## Convert and combine

```bash
# One clip to MP4 (H.264, plays everywhere, starts streaming before it fully loads)
ffmpeg -y -i .ui-review/video/after/after.webm -c:v libx264 -pix_fmt yuv420p -movflags +faststart .ui-review/after.mp4

# Before and after side by side in one file
ffmpeg -y -i .ui-review/video/before/before.webm -i .ui-review/video/after/after.webm \
  -filter_complex "[0:v][1:v]hstack=inputs=2[v]" -map "[v]" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart .ui-review/before-after.mp4
```

The two clips rarely have the same length. `hstack` ends at the shorter input by default, so record both with the same trailing pause. To label the halves, add `drawtext=text='Before':x=20:y=20:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.5` to each input before `hstack`; if ffmpeg was built without `drawtext`, put the labels in the report caption instead.

Watch the result once before shipping it: the cursor is visible, the press lands on the right control, and nothing renders a loading spinner where the real interaction would not.
