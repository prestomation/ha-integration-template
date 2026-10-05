---
title: Services and events rules
summary: How to add a service, a websocket command, an event or another surface that integrators use.
---

# Services and events rules

How the surfaces work is in [events-api](../../docs/design/events-api.md). Integrators read
[INTEGRATING.md](../../docs/INTEGRATING.md) and [EVENTS.md](../../docs/EVENTS.md).

## Services are the contract

- **Every action that changes or exports data is an `example_integration.*` service.**
  Automations, scripts, voice assistants and other integrations build on services. A
  websocket command is only a UI speed-up and never replaces a service.
- **A new action is a service first.** Write the handler in `__init__.py`, register it in
  `_register_services`, add a `ServiceSpec` to `api_surface.SERVICES`, add a
  `services.yaml` entry, and add `strings.json` text with parity in every
  `translations/<lang>.json`. hassfest and the parity test enforce the text.
- A websocket command, if any, calls the same `ExampleStore` method. Never give it a
  second code path. Add a `WebsocketSpec` that names the service it pairs with.
- **Record the privilege of each new surface.** Set `admin_only` in `api_surface.py`,
  and give the reason in the PR's Security section
  ([architecture.md](architecture.md#how-to-decide)).
- `async_unload_entry` removes the services that `api_surface.SERVICE_NAMES` lists, so a
  service in the model is torn down with no second edit.
- A read-only or report service uses `SupportsResponse.ONLY` or `OPTIONAL`. A mutation
  refreshes the coordinator exactly as the matching CRUD service does.
- A handler finds the coordinator for each call and raises the localized `not_loaded`
  error while no entry is loaded.

## Events

- **Every state change fires an `example_integration_<noun>_<verb>` event.** Build the
  payload with a pure function in `events.py`, so tests and integrators check the payload
  that ships.
- **Fire at the `store.py` chokepoint**, not in a handler, so every surface is observed
  the same way: the panel, a service call and a websocket command.
- Payloads share a spine (`events.item_event_data`). A specific event extends it, for
  example `item_updated` adds `changed_fields`. Copy a list into a payload. Never alias
  the caller's list.
- An update that changes no field fires no event.
- An event needs no new service. It observes a change that a service already makes.
- **A new event is not done until `docs/EVENTS.md` describes it**: when it fires, its
  payload, and an example automation.

## The declared surface

- **`api_surface.py` declares every surface an integrator can touch**: services, events
  and payloads, device triggers, entity platforms and attributes, options, websocket
  commands and HTTP views. A new one is not done until it has a spec there.
  `tests/unit/test_api_surface.py` parses the source and fails on drift.
- **The runtime reads the model.** Never write a second literal list beside a modelled
  one.
- **The model holds names and structure only.** Labels and descriptions come from
  `services.yaml` and `strings.json`. Never put a user-facing sentence in
  `api_surface.py`. `EventSpec.summary` is the 1 exception, because a bus event has no
  Home Assistant string source.
- `api_surface.py` imports `const` and nothing else from the integration, and nothing
  from Home Assistant.
- **The API reference is generated, never written.** `ci/generate_api_docs.py` renders it
  into the gitignored `website/developer/`. A canonical doc links to it by its site URL.
- `SURFACE_KINDS` also lists the surfaces that the integration does not offer, each with
  a reason. A new kind of surface gets a row there first.
- A device-facing event also needs a trigger in a device trigger platform, with
  `strings.json` `device_automation` labels at full translation parity, and a
  `DeviceTriggerSpec`.

## Errors and escaping

- A service handler raises a localized `ServiceValidationError` for bad input
  ([architecture.md](architecture.md#localized-text)). A websocket command answers with
  `connection.send_error`.
- Escape all user content with `escapeHTML` before it goes into `innerHTML`
  ([frontend.md](frontend.md#markup-and-text)).
