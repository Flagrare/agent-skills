// Usage: node <skill>/scripts/compose.mjs <outRoot> <baseVariant> <otherVariant> <outDir> <file>[:x,y,w,h] [more files...]
//   node .../compose.mjs ./shots main pr-tokens ./for-design modifiers.en.1280.png:190,80,900,600 flyout.en.1280.png
// Draws the two screenshots (optionally cropped) side by side with the variant names as labels.
// Labels come from --labels "main (today)|design-system PR" when the variant ids are not human enough.
import fs from 'node:fs';
import path from 'node:path';
import { playwright } from './lib.mjs';

const args = process.argv.slice(2);
const li = args.indexOf('--labels');
const labels = li >= 0 ? args.splice(li, 2)[1].split('|') : null;
const [outRoot, base, other, outDir, ...specs] = args;
if (!outRoot || !base || !other || !outDir || !specs.length) throw new Error('usage: compose.mjs <outRoot> <base> <other> <outDir> <file>[:x,y,w,h]...');
fs.mkdirSync(outDir, { recursive: true });
const dataUrl = f => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
const browser = await playwright.chromium.launch();
const page = await browser.newPage();
for (const spec of specs) {
  const [file, cropSpec] = spec.split(':');
  const crop = cropSpec ? cropSpec.split(',').map(Number) : null;
  const png = await page.evaluate(async ([ua, ub, crop, la, lb]) => {
    const load = src => new Promise(res => { const i = new Image(); i.onload = () => res(i); i.src = src; });
    const [ia, ib] = await Promise.all([load(ua), load(ub)]);
    const [x, y, w, h] = crop || [0, 0, Math.max(ia.width, ib.width), Math.max(ia.height, ib.height)];
    const gap = 24, label = 36;
    const c = document.createElement('canvas'); c.width = w * 2 + gap; c.height = h + label;
    const ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
    ctx.fillStyle = '#000'; ctx.font = 'bold 20px sans-serif'; ctx.fillText(la, 0, 26); ctx.fillText(lb, w + gap, 26);
    ctx.drawImage(ia, x, y, w, h, 0, label, w, h); ctx.drawImage(ib, x, y, w, h, w + gap, label, w, h);
    ctx.strokeStyle = '#ddd'; ctx.strokeRect(0.5, label + 0.5, w - 1, h - 1); ctx.strokeRect(w + gap + 0.5, label + 0.5, w - 1, h - 1);
    return c.toDataURL('image/png');
  }, [dataUrl(path.join(outRoot, base, file)), dataUrl(path.join(outRoot, other, file)), crop, labels?.[0] || base, labels?.[1] || other]);
  const out = path.join(outDir, file.replace(/\.png$/, `.${base}-vs-${other}.png`));
  fs.writeFileSync(out, Buffer.from(png.split(',')[1], 'base64'));
  console.log('wrote', out);
}
await browser.close();
