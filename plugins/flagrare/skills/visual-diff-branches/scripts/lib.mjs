// Shared helpers. Playwright is resolved from the PROJECT (cwd), not from the skill folder,
// so these scripts run from anywhere as long as cwd is the project root.
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const requireFromProject = createRequire(path.join(process.cwd(), 'package.json'));
export const playwright = requireFromProject('@playwright/test');

export async function loadConfig(configPath) {
  const mod = await import(pathToFileURL(path.resolve(configPath)).href);
  return mod.default || mod;
}

export function shotFile(outRoot, variant, shot, locale, viewport) {
  return path.join(outRoot, variant, `${shot}.${locale}.${viewport}.png`);
}

export async function newContext(browser, config, { locale, viewport }) {
  const base = { ...playwright.devices['Desktop Chrome'], baseURL: config.baseUrl, viewport: { width: viewport.width, height: viewport.height } };
  if (config.storageState) base.storageState = config.storageState;
  if (locale.browserLocale) base.locale = locale.browserLocale;
  const extra = typeof config.contextOptions === 'function' ? await config.contextOptions({ locale, viewport }) : config.contextOptions || {};
  return browser.newContext({ ...base, ...extra });
}

export async function settle(page, ms = 800) {
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(ms);
}

export function withLocale(url, locale) {
  return locale.apply ? locale.apply(url) : url;
}
