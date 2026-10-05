---
title: Frontend rules
summary: Rules for the panel and the card - routing, markup, bundles, i18n, layout and Home Assistant elements.
---

# Frontend rules

How the panel and the card work is in [frontend](../../docs/design/frontend.md).

## Routing

- **The URL is the source of truth.** Every page maps to a URL under
  `/example-integration`: `/` is the list and `/items/<id>` is the detail. The `set route`
  setter is the only place that changes the view state. Never set it directly to
  navigate: that puts the URL out of step and breaks Back.
- Navigate with `_navigate(state, replace?)`. It calls `history.pushState` or
  `replaceState` and fires a bubbling, composed `location-changed` event. Opening a detail
  pushes. Closing a detail or deleting an item replaces, so Back moves inside the panel.
- Keep `parseRoute` and `buildPath` pure in `utils.ts`, so they unit-test and round-trip.
  An unknown path falls back to the list. A detail URL for a deleted item shows the gone
  notice.
- **A new URL segment keeps old URLs working.** A user can bookmark any panel URL.
- Forms are not deep-linked. A form is a short-lived overlay on its page.

## Markup and text

- Escape all user content with `escapeHTML` before it goes into `innerHTML`.
- The frontend has no runtime dependencies. Rollup inlines the locale tables, so the UI
  works offline.
- All UI text comes from `t()` and `tn()` in `i18n.ts`. A lookup falls back to English and
  then to the raw key, so a missing translation never renders `undefined`.

## Bundles and the card

- 2 IIFE bundles ship from 1 static path: the panel (`example-panel.js`, loaded through
  the panel's `module_url`) and the card (`example-card.js`, added through
  `card.async_register_card`).
- `add_extra_js_url` is fire-and-forget. On a cold frontend the card element can upgrade
  after the dashboard renders, and Home Assistant then shows an error card that does not
  retry. The e2e helper `openCard` retries with a reload. Do not remove the retry.
- The extra-module `<script>` shows only after onboarding, so check it with an
  authenticated page load, not with `curl /`. The Docker tier seeds a config entry for
  the card ([testing.md](testing.md#the-seeded-fixture)).
- **Never tear down the panel or the card resource on unload.** Most unloads are half of
  a reload.

## Layout

- **Only CSS picks the layout.** Breakpoints are viewport `@media` queries. Nothing in
  `_render()` reads the viewport.
- Review each changed surface at desktop and phone width
  ([pr-workflow.md](pr-workflow.md#screenshots-desktop-and-phone)).
- State shown by color has a text equivalent.
- Do not declare a widget role that you have not implemented.

## Home Assistant elements

- **Use only HA elements that a custom panel page registers.** Check with
  `customElements.get('<tag>')` in the e2e container. Otherwise build from plain DOM and
  theme variables.
- **Probe a real element before you design against it.** `observedAttributes` tells you
  what it still reads. Assert on rendered pixels, not markup, where HA draws.
- Read each color from a Home Assistant theme variable, with a literal color only as
  the `var()` fallback, so the panel and the card follow the light and dark themes.
