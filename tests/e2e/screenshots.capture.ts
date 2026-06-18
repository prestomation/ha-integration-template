/**
 * One-off screenshot capture for PR/README embedding (the screenshot hard gate).
 *
 * Run via `screenshots.config.ts` against a running HA (see ci/e2e-up.sh with
 * KEEP_UP=1). Writes PNGs to ../../docs/images/. Add a capture block here in the
 * same PR whenever you add or change a UI surface.
 */
import { test } from '@playwright/test';
import { addItem, openCard, openPanel } from './tests/helpers';

const OUT = '../../docs/images';

test('capture: panel list with items', async ({ page }) => {
  await openPanel(page);
  // Seed a few items so the screenshot is representative.
  await addItem(page, 'Garage shelf', 4);
  await addItem(page, 'Kitchen drawer', 12);
  await addItem(page, 'Attic box', 2);
  const panel = page.locator('example-panel').first();
  await panel.locator('.ex-row').first().waitFor();
  await page.screenshot({ path: `${OUT}/panel-list.png`, fullPage: false });
});

test('capture: panel item detail', async ({ page }) => {
  await openPanel(page);
  const panel = page.locator('example-panel').first();
  await panel.locator('.detail-open').first().click();
  await panel.locator('#back-btn').waitFor();
  await page.screenshot({ path: `${OUT}/panel-detail.png`, fullPage: false });
});

test('capture: dashboard card', async ({ page }) => {
  const card = await openCard(page);
  await card.locator('ha-card').first().screenshot({ path: `${OUT}/card.png` });
});
