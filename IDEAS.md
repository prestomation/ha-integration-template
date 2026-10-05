---
title: Ideas and open work
summary: The single backlog of template work that is not built, for maintainers and agents.
---

# Ideas and open work

This file is the only list of work that is not built: gaps, refactors and ideas. Nothing
here is committed scope. When an item ships, remove it. The design docs in
`docs/design/` describe what is built.

## Home Assistant practice

- **Register the services in `async_setup`.** Home Assistant's `action-setup` rule asks
  for it, so a call during a reload gets a clear error, not "action not found". The
  handlers already find the coordinator for each call. Then keep the services through an
  unload, and drop the teardown loop in `async_unload_entry`
  (see `docs/design/architecture.md`).
- **Admin-only panel.** The panel is administration, but it is registered with
  `require_admin=False`. Register it with `require_admin=True` and gate the mutating
  services, or say in the docs why the example keeps them open (see `docs/SECURITY.md`).
- **Serve the bundles from a `dist/` directory.** The static path serves the whole
  `frontend/` directory, and in a development checkout that includes the sources. Build
  into `frontend/dist/` and serve only that.

## Localized websocket errors

`connection.send_error` in `websocket_api.py` sends a literal English message, and the
panel shows it as is. Resolve the message from a backend string table in the user's
language, and add a pure-AST test that fails on a literal message, as
`tests/unit/test_exception_translations.py` does for `raise`.

## Config and options flow

The config flow is 1 step with no input. A real integration usually adds an options
flow (`async_get_options_flow`) for its settings. Return a merge of `entry.options` and
the form input, never `user_input` ([architecture rules](.amazonq/rules/architecture.md#options)).
Add each key to `api_surface.OPTIONS`.

## More entity platforms

Only `sensor` ships. A real integration can add `binary_sensor`, `button`, `number`,
`todo`, `calendar` and others. Add the platform module, list it in `const.PLATFORMS`,
drive it from the coordinator, and anchor each `unique_id` to the item `id`. Per-item
device pages (`DeviceInfo`) are a next step.

## Device triggers for events

The events are global. If items map to devices, add device triggers (a
`device_trigger` platform) with `strings.json` `device_automation` labels at
translation parity, so the visual automation editor lists them. Add a
`DeviceTriggerSpec` for each one.

## Diagnostics redaction

`diagnostics.py` returns every item, because the item model holds no secret. If your
model stores a credential, wrap the output with
`homeassistant.components.diagnostics.async_redact_data`.

## Cross-integration contribution API

A stable interface for other integrations to push items here, such as a dispatcher
signal and a `contribute_item` service, is not built. If you need it, add a
`SIGNAL_ITEM_CONTRIBUTION` constant and a documented service. Never let a caller write
to the store directly.

## Test tiers

- **Upgrade tier.** Boot a frozen older Home Assistant on a seeded config dir, then the
  current one on the same dir. Add it when the integration stores data that Home
  Assistant migrates ([testing rules](.amazonq/rules/testing.md#writing-a-test-that-can-fail)).
- **Property-based tests.** Add `hypothesis` tests for a claim about a whole domain, such
  as "`models.apply_update` never changes a field that the update does not name". Keep
  them in `tests/unit/test_*_properties.py` with a `property` marker.
- **Phone walkthrough.** The walkthrough records 1 desktop tour. Add a phone tour with
  its own context, because `recordVideo.size` is fixed per context.

## More locales

The template ships `en` and `de` to exercise the parity gates. Add a locale with a
`<lang>.json` next to the English source (backend `translations/` and frontend
`src/locales/`), and list the frontend one in `locales/index.ts`. The parity tests then
require full coverage.
