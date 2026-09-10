// Example shots config (partner-frontend, SKU pages). Copy next to your project and edit.
// Everything project-specific lives here; the skill scripts never hardcode a URL or a venue.
const venue = '283302'; // a venue the saved e2e session can open without being logged out

const pickMenuWithItems = async page => {
  const trigger = page.locator('.menu-selector__trigger');
  if (!(await trigger.count())) return;
  await trigger.click({ timeout: 8_000 });
  const desktop = page.locator('.menu-selector__dropdown-content .menu-selector__item-name');
  const mobile = page.locator('.mobile-action-sheet__option-label');
  const items = (await desktop.count()) ? desktop : mobile;
  for (let i = 0; i < (await items.count()); i += 1) {
    if (!/unused|add menu/i.test(await items.nth(i).innerText())) { await items.nth(i).click(); return; }
  }
};

export default {
  baseUrl: 'http://localhost:4545',
  storageState: 'playwright/.auth/user.json', // refresh with: pnpm exec playwright test --project=setup
  settleMs: 800,
  isLoggedOut: page => page.locator('input[type=password]').count().then(n => n > 0),
  locales: [
    { id: 'en' },
    { id: 'ja', browserLocale: 'ja-JP', apply: url => `${url}${url.includes('?') ? '&' : '?'}language=ja` },
  ],
  viewports: [
    { id: '1280', width: 1280, height: 900 },
    { id: '390', width: 390, height: 844 },
  ],
  shots: [
    { name: 'items', url: `/items/${venue}?tab=items`, after: pickMenuWithItems },
    { name: 'item-flyout', url: `/items/${venue}?tab=items`, after: async page => { await pickMenuWithItems(page); await page.locator('.sku-item-row').first().click({ timeout: 8_000 }); await page.locator('.flyout__header').waitFor({ timeout: 8_000 }); } },
    { name: 'modifiers', url: `/items/${venue}?tab=modifiers` },
    { name: 'modifier-editor', url: `/items/${venue}?tab=modifiers`, after: async page => { await page.locator('table tbody tr').first().locator('td').first().click({ timeout: 8_000 }); await page.waitForURL(/\/modifiers\/skumgrp/, { timeout: 8_000 }); } },
    { name: 'orders', url: `/orders/${venue}` },
    { name: 'payout-report', url: `/stats/reports/payouts/orders?venueId=${venue}` },
  ],
  // Computed-style targets. Locators are functions of page so they can use any Playwright API.
  measurements: [
    {
      name: 'modifiers', url: `/items/${venue}?tab=modifiers`, viewport: '1280',
      targets: {
        tabActive: { locator: page => page.getByText('Modifiers', { exact: true }).first() },
        newButton: { locator: page => page.getByRole('button', { name: /New Modifier/ }), box: true },
        th: { locator: page => page.locator('th').first(), box: true },
        td: { locator: page => page.locator('tbody td').first(), box: true },
        availabilityPill: { locator: page => page.locator('tbody').getByText('Available').first().locator('xpath=ancestor::button[1]'), box: true },
      },
    },
    {
      name: 'editor', url: `/items/${venue}?tab=modifiers`, viewport: '1280',
      after: async page => { await page.locator('table tbody tr').first().locator('td').first().click({ timeout: 8_000 }); await page.waitForURL(/\/modifiers\/skumgrp/, { timeout: 8_000 }); },
      targets: {
        sectionTitle: { locator: page => page.getByText('Modifier details', { exact: true }) },
        label: { locator: page => page.getByText('Modifier name', { exact: true }) },
        input: { locator: page => page.locator('input[type=text], input:not([type])').first(), box: true },
        ruleRow: { locator: page => page.getByText('Make modifier selection required') },
        cancel: { locator: page => page.getByRole('button', { name: 'Cancel' }), box: true },
        save: { locator: page => page.getByRole('button', { name: 'Save changes' }), box: true },
      },
    },
  ],
};
