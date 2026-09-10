// Usage: node <skill>/scripts/measure.mjs <shots.mjs> <variant> <outRoot>
// Records computed styles for every target in config.measurements and writes <outRoot>/measure.<variant>.json.
// Pixel diffs say WHERE something changed; this says WHAT (font-size, radius, colour, height...).
import fs from 'node:fs';
import path from 'node:path';
import { loadConfig, newContext, playwright, settle, withLocale } from './lib.mjs';

const [configPath, variant, outRoot] = process.argv.slice(2);
if (!configPath || !variant || !outRoot) throw new Error('usage: measure.mjs <shots.mjs> <variant> <outRoot>');
const config = await loadConfig(configPath);
fs.mkdirSync(outRoot, { recursive: true });
const browser = await playwright.chromium.launch();
const out = {};
for (const group of config.measurements || []) {
  const locale = config.locales.find(l => l.id === (group.locale || config.locales[0].id));
  const viewport = config.viewports.find(v => v.id === (group.viewport || config.viewports[0].id));
  const context = await newContext(browser, config, { locale, viewport });
  const page = await context.newPage();
  try {
    await page.goto(withLocale(group.url, locale), { waitUntil: 'domcontentloaded' });
    await settle(page, config.settleMs);
    if (group.after) { await group.after(page); await settle(page, config.settleMs); }
    for (const [key, target] of Object.entries(group.targets)) {
      const el = target.locator(page).first();
      out[`${group.name}.${key}`] = (await el.count()) ? await el.evaluate((e, box) => {
        const s = getComputedStyle(e); const r = e.getBoundingClientRect();
        const o = { text: (e.textContent || '').trim().slice(0, 24), fontSize: s.fontSize, fontWeight: s.fontWeight, lineHeight: s.lineHeight, color: s.color, letterSpacing: s.letterSpacing };
        if (box) Object.assign(o, { bg: s.backgroundColor, border: `${s.borderTopWidth} ${s.borderTopStyle} ${s.borderTopColor}`, radius: s.borderRadius, padding: s.padding, height: `${Math.round(r.height)}px`, width: `${Math.round(r.width)}px` });
        return o;
      }, Boolean(target.box)) : null;
    }
  } catch (error) {
    console.log(`FAIL ${group.name}: ${String(error).split('\n')[0]}`);
  }
  await context.close();
}
await browser.close();
const file = path.join(outRoot, `measure.${variant}.json`);
fs.writeFileSync(file, JSON.stringify({ variant, out }, null, 1));
console.log(`wrote ${file} (${Object.keys(out).length} targets, ${Object.values(out).filter(v => !v).length} not found)`);
