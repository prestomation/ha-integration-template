import { test, expect } from '@playwright/test';
import { addItem, openCard, openPanel, trackPanelErrors } from './helpers';

test.describe('Example Integration panel — smoke', () => {
  test('panel renders with title, add button, and no errors', async ({ page }) => {
    const errors = trackPanelErrors(page);
    await openPanel(page);
    const panel = page.locator('example-panel').first();
    await expect(panel.locator('.ex-toolbar-title')).toContainText('Example Integration');
    await expect(panel.locator('#add-btn')).toBeVisible();
    expect(errors, `panel errors:\n${errors.join('\n')}`).toHaveLength(0);
  });

  test('adding an item shows it in the list', async ({ page }) => {
    await openPanel(page);
    await addItem(page, 'Garage shelf', 7);
    const panel = page.locator('example-panel').first();
    await expect(panel.locator('.ex-row', { hasText: 'Garage shelf' })).toBeVisible();
  });
});

test.describe('Example Integration panel — deep linking & Back', () => {
  test('opening an item reflects in the URL', async ({ page }) => {
    await openPanel(page);
    await addItem(page, 'Link target', 1);
    const panel = page.locator('example-panel').first();
    await panel.locator('.detail-open', { hasText: 'Link target' }).first().click();
    await expect(panel.locator('#back-btn')).toBeVisible();
    await expect(page).toHaveURL(/\/example-integration\/items\/.+$/);
  });

  test('browser Back returns to the list, not out of the panel', async ({ page }) => {
    await openPanel(page);
    await addItem(page, 'Back target', 2);
    const panel = page.locator('example-panel').first();
    await panel.locator('.detail-open', { hasText: 'Back target' }).first().click();
    await expect(panel.locator('#back-btn')).toBeVisible();
    await page.goBack();
    await expect(page).toHaveURL(/\/example-integration(\/)?$/);
    await expect(panel.locator('#add-btn')).toBeVisible();
  });
});

test.describe('Example Integration — dashboard card', () => {
  test('the custom card renders on the dashboard', async ({ page }) => {
    const card = await openCard(page);
    await expect(card.locator('ha-card').first()).toBeVisible();
  });
});
