# Architecture & code conventions

These rules describe the conventions to follow when generating or reviewing code
in this repository (the `example_integration` Home Assistant integration
template). They are deliberately generic so they survive renaming the template to
your own domain.

## Separation of administration vs. usage
- **Administration** lives in the custom **sidebar panel**
  (`frontend/`, a `panel_custom`-style built-in custom panel). Create/edit/delete
  of items belongs here.
- **Usage / display** is surfaced through **native Home Assistant entities** (the
  `sensor` platform) and the **dashboard card**. Prefer native entities + HA's
  built-in cards for read surfaces; keep management UI in the panel, not the card.

## Pure, HA-free core
- `models.py` and `events.py` MUST NOT import anything from `homeassistant`. They
  are pure Python so they can be unit-tested without the HA test harness
  (`tests/unit`, `pip install pytest`). Inject HA specifics (the current time via
  `dt_util`, validation at the boundary) from the callers instead.
- Keep them deterministic: pass values like timestamps in (e.g. `build_item(...,
  created=dt_util.now().isoformat())`) rather than reading a clock internally.

## One mutation chokepoint
- All item writes go through `ExampleStore` (`store.py`). Entities and the panel
  read via the `ExampleCoordinator` and never mutate storage directly.
- Items are plain JSON-serializable dicts (never model objects in storage):
  `id, name, value, created`.
- For a local store with no I/O cost, mutations call `await
  coordinator.async_refresh()` (immediate, awaited, deterministic) — not the
  debounced `async_request_refresh()`, whose cooldown collapses rapid mutations
  and makes tests non-deterministic.

## Entities
- Entity `unique_id`s are anchored to the item `id` so they survive renames. The
  per-item entity set is reconciled on each coordinator refresh (new items add an
  entity; removed items' entities go unavailable and are pruned on reload).
- Use `has_entity_name` + a `translation_key` for fixed entities (e.g. the total
  sensor) so their names localize via `strings.json`.

## Services are the interoperability surface — expose every action as one
- **Every action that mutates or exports data MUST be an `example_integration.*`
  Home Assistant service**, not only a panel websocket command. Services are what
  automations, scripts, voice assistants, and other integrations build on.
- **New action ⇒ service first.** It lands as a service (handler in `__init__.py`,
  registered in `_register_services`, listed in `_SERVICES` for teardown) *and*
  documented: a `services.yaml` entry plus `strings.json` localization at parity
  across all `translations/<lang>.json` (the parity test + hassfest enforce this).
  Any websocket command is added alongside and delegates to the same
  `ExampleStore` method — never a divergent code path.
- Read-only/report services use `SupportsResponse.ONLY`/`OPTIONAL`; mutations
  refresh the coordinator exactly as the equivalent CRUD service does.

## Events are the observation surface — fire one for every state change
- **Every observable state change fires a documented
  `example_integration_<noun>_<verb>` bus event**, built by a **pure function in
  `events.py`** (no HA imports) so tests and integrators assert against the exact
  shipped payload. Fire at the **`store.py` mutation chokepoint**, not in a service
  handler, so every surface (panel, service, websocket) is observed uniformly.
- Payloads share a common **spine** (`events.item_event_data`); specific events
  extend it (e.g. `item_updated` adds `changed_fields`). Don't alias the caller's
  list into the payload — copy it.
- **Keep the catalog in sync.** A new event isn't done until it's in
  [`docs/EVENTS.md`](../../docs/EVENTS.md) (when it fires, payload, semantics).
  Events are observations of changes that already flow through the store, so they
  need **no** new service.

## Panel navigation & deep linking
- The panel's navigation state is **deep-linked**: every navigable destination maps
  to a URL under the panel prefix (`/example-integration`). Scheme: `/` (list),
  `/items/<id>` (detail). Forms are ephemeral overlays and are not deep-linked.
- **The URL is the single source of truth.** HA hands the panel a `route` for every
  in-panel URL change, including Back/Forward. The `route` setter parses `path` and
  is the *only* place that flips the view/detail state. Never mutate it directly to
  navigate — that desyncs the URL and breaks Back.
- **Navigate by changing the URL** via a `_navigate` helper
  (`history.pushState`/`replaceState` + a bubbling `composed` `location-changed`
  event). Drill-in (open a detail) **pushes**; lateral moves and detail-close/delete
  **replace**, so Back never retraces and moves within the panel instead of ejecting.
- Keep route parse/build as **pure functions in `utils.ts`** (`parseRoute`,
  `buildPath`) so they unit-test and round-trip losslessly. Unknown/empty paths
  fall back to the list; a detail URL whose id no longer exists renders a "gone"
  notice rather than erroring.

## Frontend bundles & the card-load race
- Two IIFE bundles ship from one static path: the panel (`example-panel.js`, loaded
  via the panel's `module_url`) and the card (`example-card.js`, auto-registered as
  an extra module URL via `card.async_register_card` → `frontend.add_extra_js_url`).
- `add_extra_js_url` injection is **fire-and-forget**: on a cold frontend the custom
  card element may not upgrade before Lovelace renders the dashboard, so HA shows a
  non-retrying error card. e2e helpers handle this with a **retry-with-reload** (see
  `tests/e2e/tests/helpers.ts` `openCard`); don't "fix" it by removing the retry.
- The integration must be set up **at HA startup** for the card resource to be
  injected before dashboards render — i.e. a config entry must already exist when HA
  boots. The Docker/e2e tiers seed one at
  `tests/integration/ha_config/.storage/core.config_entries` (the only tracked
  `.storage` file). Creating the entry at runtime is too late: the card resource
  won't be injected into the onboarded app shell. Note the extra-module `<script>`
  only appears once onboarding is complete, so verify via a real (authenticated)
  page load, not a bare `curl /`.

## Errors, validation & security
- Service handlers raise `ServiceValidationError` for user-facing errors; the pure
  model raises `ItemValidationError`, translated at the boundary. Websocket commands
  return structured errors via `connection.send_error`.
- Escape all user-provided content before injecting into `innerHTML` in the panel
  (`escapeHTML`).

## Version single-source-of-truth
- `manifest.json` `version` is canonical. `const.py` `PANEL_VERSION` mirrors it and
  `release.yml` asserts they match; `rollup.config.mjs` reads `PANEL_VERSION` from
  `const.py` so the bundles are stamped consistently. Bump both in one PR.
