# `shots.mjs` contract

Default-export an object. All paths are relative to the project root (the scripts' working directory).

```js
export default {
  baseUrl: 'http://localhost:4545',
  storageState: 'playwright/.auth/user.json',   // optional; whatever your login setup writes
  settleMs: 800,                                 // extra wait after networkidle, per navigation
  contextOptions: ({ locale, viewport }) => ({}),// optional extra Playwright context options
  isLoggedOut: async page => (await page.locator('input[type=password]').count()) > 0, // optional tell

  locales: [
    { id: 'en' },
    { id: 'ja', browserLocale: 'ja-JP', apply: url => `${url}${url.includes('?') ? '&' : '?'}language=ja` },
  ],
  viewports: [
    { id: '1280', width: 1280, height: 900 },
    { id: '390', width: 390, height: 844 },
  ],

  shots: [
    { name: 'list', url: '/things' },
    { name: 'editor', url: '/things', after: async (page, { locale, viewport }) => {
        await page.locator('table tbody tr').first().click({ timeout: 8_000 });
        await page.waitForURL(/\/things\/\w+/, { timeout: 8_000 });
    } },
  ],

  measurements: [
    { name: 'list', url: '/things', locale: 'en', viewport: '1280',   // locale/viewport default to the first of each
      after: async page => {},                                        // optional, same as shots
      targets: {
        th:     { locator: page => page.locator('th').first(), box: true },
        button: { locator: page => page.getByRole('button', { name: 'Save' }), box: true },
        label:  { locator: page => page.getByText('Name', { exact: true }) },
      } },
  ],
};
```

Notes:

- `capture.mjs` produces `<outRoot>/<variant>/<shot>.<locale>.<viewport>.png`; `diff.mjs` and `compose.mjs` key on that file name, so keep shot names stable across variants.
- Context defaults come from Playwright's `devices['Desktop Chrome']` plus `baseURL`, `viewport`, `storageState` and `locale`. Some apps only accept the saved session when the context carries the same device profile the login setup used; the default covers that.
- `after` runs after the page settles and before the screenshot. Put a `timeout` on every click so a missing element fails fast instead of eating 30 s.
- Text targets record font-size, weight, line-height, colour and letter-spacing. `box: true` adds background, border, radius, padding, height and width.
- `measure.mjs` opens one context per measurement group, so groups are independent; a failing group prints `FAIL <name>` and the rest still run.
