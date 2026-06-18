# Ideas / deferred work

A scratchpad of things this template deliberately leaves out, with the hook points
to build them. Keeping them here (rather than half-built) keeps the template small
and the conventions clear.

## Config/options flow with real options
The config flow is single-step with no input. A real integration usually adds an
options flow (`async_get_options_flow`) for tunables. Hook: `config_flow.py`.

## More entity platforms
Only `sensor` ships. A real integration might add `binary_sensor`, `button`,
`number`, `todo`, `calendar`, etc. Pattern to follow: add the platform module, list
it in `const.PLATFORMS`, drive it from the coordinator, anchor `unique_id`s to the
item `id`. Per-item device pages (`DeviceInfo`) are a natural next step.

## Device triggers for events
Events are global today. If items map to devices, expose `device_trigger.py` triggers
(with `strings.json` `device_automation` labels at translation parity) so the visual
automation editor lists them.

## Diagnostics redaction
`diagnostics.py` dumps everything because the item model has no secrets. If your model
stores credentials, wrap the output with `homeassistant.components.diagnostics.async_redact_data`.

## Cross-integration contribution API (DEFERRED)
A stable interface for *other* integrations to push items here (a dispatcher signal +
a `contribute_item` service) is intentionally not built. If you need it, add a
`SIGNAL_ITEM_CONTRIBUTION` const and a documented service rather than letting callers
touch the store directly.

## More locales
The template ships `en` + `de` to exercise the parity gates. Add locales by dropping
`<lang>.json` next to the English source (backend `translations/` and frontend
`src/locales/`), wiring the frontend one into `locales/index.ts`. The parity tests
then require full coverage.
