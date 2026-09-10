// Usage (from the project root): node <skill>/scripts/capture.mjs <shots.mjs> <variant> <outRoot> [--only a,b]
// Writes <outRoot>/<variant>/<shot>.<locale>.<viewport>.png (full page) and prints one line per shot
// with the rendered size, so outliers (a spinner caught mid-load, a login page) stand out.
import fs from 'node:fs';
import path from 'node:path';
import { loadConfig, newContext, playwright, settle, shotFile, withLocale } from './lib.mjs';

const [configPath, variant, outRoot, ...rest] = process.argv.slice(2);
if (!configPath || !variant || !outRoot) throw new Error('usage: capture.mjs <shots.mjs> <variant> <outRoot> [--only a,b]');
const only = rest.includes('--only') ? rest[rest.indexOf('--only') + 1].split(',') : null;
const config = await loadConfig(configPath);
const shots = config.shots.filter(s => !only || only.includes(s.name));
fs.mkdirSync(path.join(outRoot, variant), { recursive: true });

const browser = await playwright.chromium.launch();
const failures = [];
for (const locale of config.locales) {
  for (const viewport of config.viewports) {
    const context = await newContext(browser, config, { locale, viewport });
    const page = await context.newPage();
    for (const shot of shots) {
      const file = shotFile(outRoot, variant, shot.name, locale.id, viewport.id);
      try {
        await page.goto(withLocale(shot.url, locale), { waitUntil: 'domcontentloaded' });
        await settle(page, config.settleMs);
        if (shot.after) { await shot.after(page, { locale, viewport }); await settle(page, config.settleMs); }
        if (config.isLoggedOut && (await config.isLoggedOut(page))) throw new Error('landed on the login page (session expired or this URL logs the user out)');
        await page.screenshot({ path: file, fullPage: true });
        const size = await page.evaluate(() => `${document.documentElement.scrollWidth}x${document.documentElement.scrollHeight}`);
        console.log(`ok   ${path.basename(file).padEnd(40)} ${size}`);
      } catch (error) {
        failures.push(path.basename(file));
        console.log(`FAIL ${path.basename(file).padEnd(40)} ${String(error).split('\n')[0]}`);
      }
    }
    await context.close();
  }
}
await browser.close();
if (failures.length) { console.log(`\n${failures.length} failed`); process.exitCode = 1; }
