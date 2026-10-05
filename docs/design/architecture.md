---
title: Architecture
summary: How the example integration splits into a pure core and Home Assistant glue, and how it sets up.
implements:
  - custom_components/example_integration/__init__.py
  - custom_components/example_integration/const.py
  - custom_components/example_integration/config_flow.py
  - custom_components/example_integration/diagnostics.py
related: [store, coordinator-entities, events-api, frontend]
source_hash: bd2652c92d44
---

# Architecture

Example Integration is a template for a Home Assistant custom integration. Its feature
is an items list. Each item has a name and an integer value. Admins manage the items in a
sidebar panel. Users read them through native `sensor` entities and a dashboard card.
The feature is small on purpose: the structure around it is the subject.

## Goals

- **G1. Testable core.** The model and the event payloads run without Home Assistant, so
  the fast unit tier and the mutation gate can check them.
- **G2. One write path.** Every change to the data goes through 1 store method that
  validates, saves and fires its event.
- **G3. Services first.** Each data action is an `example_integration.*` service, so
  automations, scripts, voice and other integrations can do what the panel does.
- **G4. Native usage.** Daily use goes through native entities and the card. The panel is
  for administration.
- **G5. Easy to fork.** `scripts/rename.py` turns the template into a new integration in
  1 command, and every gate keeps working after the rename.

## Non-goals

- A real feature. The items list exists to show the patterns.
- More than 1 config entry. `config_flow.ExampleConfigFlow` sets a fixed unique id.
- Options. The template has no options flow ([IDEAS.md](../../IDEAS.md)).
- A `quality_scale` tier in the manifest. The tier depends on the domain of the fork.

## Design

### Module map

| Layer | Modules | Rule |
|---|---|---|
| Pure core | `models.py`, `events.py`, `const.py`, `api_surface.py` | No `homeassistant` import. The time comes in as an argument. |
| Boundary | `store.py`, `coordinator.py` | Talks to Home Assistant storage and the bus, and calls into the core. |
| Glue | `__init__.py`, `websocket_api.py`, `panel.py`, `card.py`, `config_flow.py`, `diagnostics.py` | Registers surfaces with Home Assistant. |
| Platforms | `sensor.py` | `const.PLATFORMS` lists them. |

The mutation allowlist (`only_mutate` in `pyproject.toml`) is drawn from the first row.
`api_surface.py` declares each surface that an integrator sees ([events-api](events-api.md)).

### Setup

`async_setup` does nothing: the integration has no YAML configuration.
`async_setup_entry` runs these steps in order:

1. Create `ExampleStore` and load the stored document ([store](store.md)).
2. Create `ExampleCoordinator`, run its first refresh, and store it as
   `entry.runtime_data` ([coordinator-entities](coordinator-entities.md)).
3. Register the panel and its static path, the card resource and the websocket
   commands ([frontend](frontend.md)).
4. Forward `const.PLATFORMS`.
5. Register the services with `_register_services`. Each handler finds the coordinator
   for each call, and raises the localized `not_loaded` error when no entry is loaded.

### Unload

`async_unload_entry` unloads the platforms. When no entry of the domain stays loaded, it
removes each service in `api_surface.SERVICE_NAMES`. It leaves the panel, the static path
and the card resource in place, because most unloads are half of a reload.

### Config entry

The config flow is 1 confirmation step with no data. A second flow aborts, because the
unique id is the domain.

### Diagnostics

`diagnostics.async_get_config_entry_diagnostics` returns the entry title, version and
domain, and every item. The item model holds no secret, so nothing is redacted. A fork
that stores a credential wraps the output with `async_redact_data`.

### Errors

The pure model raises `models.ItemValidationError`. A service handler maps it, and a
missing id, to a `ServiceValidationError` with a `translation_key` from `strings.json`
`exceptions`. A websocket command answers with `connection.send_error`.

### Privilege

The example integration has no admin-only operation. The panel is registered with
`require_admin=False`, and every service and websocket command is open to a signed-in
user ([SECURITY.md](../SECURITY.md)).

### Design doc index

| Doc | Subject |
|---|---|
| [store](store.md) | The storage document, the item model and the mutation chokepoint |
| [coordinator-entities](coordinator-entities.md) | The coordinator, the sensor platform and the service device |
| [events-api](events-api.md) | Services, events, websocket commands and the API surface model |
| [frontend](frontend.md) | The panel, the card, routing, i18n and the bundle delivery |

## Trade-offs

- **A sidebar panel** over **a dashboard card for administration**: management is a
  full-page activity with forms, and native cards already show values well.
- **Services registered at entry setup** over **services registered in `async_setup`**:
  the teardown iterates the model, so registration and removal cannot disagree. The cost
  is that a call during a reload gets "action not found" ([IDEAS.md](../../IDEAS.md)).
- **One tiny feature** over **a realistic one**: a fork deletes less code, and each
  pattern stays visible.

## One-way doors

- The domain, the panel path `/example-integration` and the static path
  `/example_integration_static`. A fork replaces them once with `scripts/rename.py`.
- The service names and fields, and the event names and payloads
  ([INTEGRATING.md](../INTEGRATING.md)).
- The storage key `example_integration` and `const.STORAGE_VERSION`.
