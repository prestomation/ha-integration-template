/**
 * One-off **video** walkthrough capture for the per-PR preview — not part of the
 * e2e suite (the filename does not match *.spec.ts, and it's only run via
 * videos.config.ts). It records a short end-to-end tour of the Example Integration
 * UI as a WebM, which ci/capture-video.sh then transcodes to mp4 (+ a GIF that
 * embeds like a screenshot) under docs/videos/.
 *
 * Run it through the wrapper (recommended — it does the ffmpeg transcode too):
 *   bash ci/capture-video.sh
 *
 * Or directly (raw WebM only), from tests/e2e/:
 *   VIDEO_DIR=../../docs/videos npx playwright test --config=videos.config.ts
 *
 * Unlike the screenshot captures, video is wired at the browser *context* level
 * (`recordVideo`) and the file is only flushed when the context closes — so this
 * spec builds its own authenticated context (reusing the auth state global-setup
 * wrote to .auth/state.json) rather than the default `page` fixture, then saves the
 * recording to a stable name we can transcode.
 *
 * The tour is coupled to the panel/card selectors. When a feature adds or changes a
 * UI surface, extend the tour here in the same PR (deliberate BEAT pauses so the
 * motion reads well), the way you'd add a block to screenshots.capture.ts.
 */
import { test, expect } from '@playwright/test';
import { resolve } from 'path';
import { openCard, openPanel } from './tests/helpers';

const OUT = process.env.VIDEO_DIR || '/tmp/example-integration-video';
const STATE_PATH = resolve(__dirname, '.auth/state.json');
const SIZE = { width: 1280, height: 800 };

/** A readable pause so motion in the recording is easy to follow. */
const BEAT = 900;

test('record Example Integration walkthrough', async ({ browser }) => {
  // Build an authenticated context that records video. The recording is flushed to
  // disk only on context.close(), after which page.video().saveAs() names it.
  const context = await browser.newContext({
    storageState: STATE_PATH,
    viewport: SIZE,
    recordVideo: { dir: OUT, size: SIZE },
  });
  const page = await context.newPage();

  try {
    // 1. Land on the admin panel — the items list (management lives in the panel).
    await openPanel(page);
    const panel = page.locator('example-panel').first();
    await expect(panel.locator('.ex-toolbar-title')).toBeVisible();
    await page.waitForTimeout(BEAT * 2);

    // 2. Add a couple of items through the panel's add form — show the form open,
    //    the fields fill, and the new rows appear.
    for (const [name, value] of [
      ['Garage shelf', 4],
      ['Kitchen drawer', 12],
    ] as const) {
      await panel.locator('#add-btn').click();
      await expect(panel.locator('#ex-item-form')).toBeVisible();
      await panel.locator('#ex-item-form #ex-name').fill(name);
      await page.waitForTimeout(BEAT);
      await panel.locator('#ex-item-form #ex-value').fill(String(value));
      await page.waitForTimeout(BEAT);
      await panel.locator('#ex-item-form #ex-save').click();
      await expect(panel.locator('.ex-name', { hasText: name }).first()).toBeVisible();
      await page.waitForTimeout(BEAT);
    }

    // 3. Open an item's detail page (deep-linked route) — the edit form — then Back.
    await panel.locator('.detail-open').first().click();
    await expect(panel.locator('#back-btn')).toBeVisible();
    await expect(panel.locator('#ex-edit-form')).toBeVisible();
    await page.waitForTimeout(BEAT * 2);
    await panel.locator('#back-btn').click();
    await expect(panel.locator('#add-btn')).toBeVisible();
    await page.waitForTimeout(BEAT);

    // 4. The usage/display surface — the dashboard card reflecting those items live.
    const card = await openCard(page);
    await expect(card.locator('ha-card').first()).toBeVisible();
    await page.waitForTimeout(BEAT * 3);
  } finally {
    // Close the context to flush the recording, then save it to a stable filename.
    await context.close();
    const video = page.video();
    if (video) await video.saveAs(resolve(OUT, 'walkthrough.webm'));
  }
});
