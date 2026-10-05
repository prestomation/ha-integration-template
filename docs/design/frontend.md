---
title: Frontend
summary: How the panel and the card are built, delivered, routed and translated.
implements:
  - custom_components/example_integration/panel.py
  - custom_components/example_integration/card.py
  - custom_components/example_integration/frontend/src/**/*.ts
related: [architecture, events-api]
source_hash: dff645e58237
---

# Frontend

The frontend is 2 web components in TypeScript, built by Rollup into 2 IIFE bundles.
The panel (`example-panel`) is the admin page in the Home Assistant sidebar. The card
(`example-card`) is a dashboard card that lists the items. Both talk to the backend
through the websocket commands ([events-api](events-api.md)).

## Goals

- **G1. The URL is the state.** Each panel page has a URL, and Back and Forward move
  inside the panel.
- **G2. No setup for the user.** The panel shows in the sidebar and the card shows in the
  card picker with no YAML and no manual resource.
- **G3. Safe markup.** User text never reaches `innerHTML` unescaped.
- **G4. Offline text.** Every locale table is in the bundle, so the UI needs no fetch to
  show text in the user's language.
- **G5. Small and testable.** No runtime dependency. The route and i18n logic are pure
  functions that vitest and Stryker check.

## Non-goals

- Administration in the card. The card reads. The panel writes.
- A framework such as Lit. The components render plain DOM strings.
- Deep links to forms. A form is an overlay on its page.

## Design

### Delivery

`panel.async_register_panel` registers the static path `const.PANEL_STATIC_URL` on the
`frontend/` directory, then registers a `custom` panel at `/example-integration` with the
module URL `example-panel.js?v=<PANEL_VERSION>`. Both steps are idempotent, so a reload
does not register them twice. `card.async_register_card` adds `example-card.js` to the
frontend's extra module URLs once per Home Assistant run.

`add_extra_js_url` does not wait for the module. On a cold frontend the card element can
upgrade after the dashboard renders, and Home Assistant then shows an error card. The
seeded config entry in the Docker tier makes the integration load at startup, which puts
the card module in the served pages.

`rollup.config.mjs` reads `PANEL_VERSION` from `const.py` and gives it to both bundles
through the `panel-version` virtual module. The version string is also the cache key in
both module URLs.

### Modules

| Module | Role |
|---|---|
| `index.ts`, `card-index.ts` | Define the custom elements. `card-index.ts` also adds the card to `window.customCards`. |
| `panel.ts` | The `ExamplePanel` element: route, data load, list, detail, add and edit forms. |
| `card.ts` | The `ExampleCard` element and its title-only editor. |
| `api.ts` | `ExampleApi`, a thin client for the websocket commands. |
| `utils.ts` | `escapeHTML`, `parseRoute`, `buildPath` and `formatDate`. Pure. |
| `i18n.ts`, `locales/index.ts` | Locale lookup, plural forms and the bundled tables. |
| `types.ts`, `global.d.ts` | Shared types. |

### Routing

Home Assistant sets `route` on the panel for each URL change in the panel, Back and
Forward included. `set route` parses it with `utils.parseRoute` and renders. The panel
changes the URL only through `_navigate`, which pushes or replaces a history entry and
fires `location-changed`. `/` is the list. `/items/<id>` is the detail, and an id that
is not in the list shows the gone page.

### Data

The panel loads the item list when it first gets `hass`, and loads it again after each of
its own writes. The card loads the list and subscribes to the 3 item events, so it shows
a change from any surface. It ends the subscriptions when it leaves the page.

### Text

`i18n.setLanguage` picks the table for the Home Assistant language: an exact match,
then the base language, then English. `t` and `tn` fall back key by key to English and
then to the key itself. `tn` picks the plural form with `Intl.PluralRules` and needs an
`.other` form for each base key.

## Trade-offs

- **Plain DOM strings with `escapeHTML`** over **a template library**: no dependency, at
  the cost of a full re-render on each change.
- **A static path for the bundles** over **a Lovelace resource in storage**: no write to
  the user's dashboards, at the cost of the load race above.
- **Locale tables in the bundle** over **a fetch per language**: a larger bundle, and no
  network failure mode.

## One-way doors

- The element names `example-panel`, `example-card` and
  `example-card-editor`. A dashboard stores the card type
  `custom:example-card` in its YAML.
- The panel URLs `/example-integration` and `/items/<id>`. Users bookmark them.
- The card config key `title`.
