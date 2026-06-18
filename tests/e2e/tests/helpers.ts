import { Page, expect } from '@playwright/test';

/** Open the Example Integration sidebar panel and wait for it to attach. */
export async function openPanel(page: Page): Promise<void> {
  await page.goto('/example-integration', { waitUntil: 'domcontentloaded' });
  await page.locator('example-panel').first().waitFor({ state: 'attached', timeout: 45_000 });
}

/** Open the seeded e2e dashboard that hosts the custom card. */
export async function openDashboard(page: Page): Promise<void> {
  await page.goto('/example-e2e/items', { waitUntil: 'domcontentloaded' });
  await page.locator('hui-view, home-assistant').first().waitFor({ state: 'attached', timeout: 45_000 });
}

/**
 * Open the dashboard and wait for the custom card to upgrade and render.
 * Returns the card locator (it lives in nested shadow DOM, which Playwright
 * pierces). The card JS is an auto-registered extra module (`add_extra_js_url`),
 * which is fire-and-forget: on the very first dashboard load of a run HA may not
 * have finished loading it, so the element doesn't upgrade in time and HA shows
 * a non-retrying error card. A reload (the module is warm by then) fixes it —
 * retry a couple of times so the first test isn't flaky on a cold frontend.
 */
export async function openCard(page: Page) {
  let lastErr: unknown;
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt === 0) await openDashboard(page);
    else await page.reload({ waitUntil: 'domcontentloaded' });
    const card = page.locator('example-card').first();
    try {
      await card.waitFor({ state: 'attached', timeout: 20_000 });
      await expect(card.locator('ha-card').first()).toBeVisible({ timeout: 20_000 });
      return card;
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr;
}

/**
 * Collect uncaught panel errors so a spec can assert the panel rendered cleanly.
 * Returns a live array of console-error + pageerror messages.
 */
export function trackPanelErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('pageerror', (err) => errors.push(String(err)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  return errors;
}

/** Add an item through the panel's add form. */
export async function addItem(page: Page, name: string, value: number): Promise<void> {
  const panel = page.locator('example-panel').first();
  await panel.locator('#add-btn').click();
  await panel.locator('#ex-item-form #ex-name').fill(name);
  await panel.locator('#ex-item-form #ex-value').fill(String(value));
  await panel.locator('#ex-item-form #ex-save').click();
  await expect(panel.locator('.ex-name', { hasText: name }).first()).toBeVisible();
}
