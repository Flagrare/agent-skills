// Usage: node <skill>/scripts/diff.mjs <outRoot> <baseVariant> <otherVariant> [more variants...]
// Pixel-diffs every <base> screenshot against the same file in each other variant, using a headless
// browser canvas (no image library needed). Writes <outRoot>/diff-<other>/<file>.png (changed pixels
// in red over a faded base) and prints one row per file: changed %, sizes, bounding box of the change.
import fs from 'node:fs';
import path from 'node:path';
import { playwright } from './lib.mjs';

const [outRoot, base, ...others] = process.argv.slice(2);
if (!outRoot || !base || !others.length) throw new Error('usage: diff.mjs <outRoot> <base> <other...>');
const files = fs.readdirSync(path.join(outRoot, base)).filter(f => f.endsWith('.png')).sort();
const dataUrl = f => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64');
const browser = await playwright.chromium.launch();
const page = await browser.newPage();
console.log(['variant', 'file', 'changed', 'base size', 'other size', 'bbox x,y,x2,y2'].join('\t'));
for (const other of others) {
  fs.mkdirSync(path.join(outRoot, `diff-${other}`), { recursive: true });
  for (const file of files) {
    const b = path.join(outRoot, other, file);
    if (!fs.existsSync(b)) { console.log([other, file, 'missing'].join('\t')); continue; }
    const r = await page.evaluate(async ([ua, ub]) => {
      const load = src => new Promise(res => { const i = new Image(); i.onload = () => res(i); i.src = src; });
      const [ia, ib] = await Promise.all([load(ua), load(ub)]);
      const w = Math.max(ia.width, ib.width), h = Math.max(ia.height, ib.height);
      const pixels = img => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, w, h); x.drawImage(img, 0, 0); return x.getImageData(0, 0, w, h).data; };
      const da = pixels(ia), db = pixels(ib);
      const out = document.createElement('canvas'); out.width = w; out.height = h; const ox = out.getContext('2d'); const od = ox.createImageData(w, h);
      let n = 0, minX = w, minY = h, maxX = 0, maxY = 0;
      for (let i = 0; i < da.length; i += 4) {
        const d = Math.abs(da[i] - db[i]) + Math.abs(da[i + 1] - db[i + 1]) + Math.abs(da[i + 2] - db[i + 2]);
        if (d > 30) { n++; const p = i / 4, y = Math.floor(p / w), x = p % w; if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; od.data[i] = 255; od.data[i + 1] = 0; od.data[i + 2] = 0; od.data[i + 3] = 255; }
        else { const g = 255 - Math.round((255 - da[i]) * 0.25); od.data[i] = g; od.data[i + 1] = g; od.data[i + 2] = g; od.data[i + 3] = 255; }
      }
      ox.putImageData(od, 0, 0);
      return { pct: (100 * n / (w * h)).toFixed(2), a: `${ia.width}x${ia.height}`, b: `${ib.width}x${ib.height}`, box: n ? [minX, minY, maxX, maxY].join(',') : '-', png: out.toDataURL('image/png') };
    }, [dataUrl(path.join(outRoot, base, file)), dataUrl(b)]);
    fs.writeFileSync(path.join(outRoot, `diff-${other}`, file), Buffer.from(r.png.split(',')[1], 'base64'));
    console.log([other, file, `${r.pct}%`, r.a, r.b, r.box].join('\t'));
  }
}
await browser.close();
