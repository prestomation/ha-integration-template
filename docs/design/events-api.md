---
title: Events and the API surface
summary: The services, bus events and websocket commands that other code uses, and the model in api_surface.py that declares them.
implements:
  - custom_components/example_integration/events.py
  - custom_components/example_integration/api_surface.py
  - custom_components/example_integration/websocket_api.py
related: [architecture, store, frontend]
source_hash: e69530f21f63
---

# Events and the API surface

The integration has 2 stable surfaces for other code: **services** to act and **bus
events** to observe. The panel and the card also use **websocket commands**, which are
internal. `api_surface.py` declares each surface once. The runtime reads it, and
`tests/unit/test_api_surface.py` fails when the source and the model disagree. The
integrator view is in [INTEGRATING.md](../INTEGRATING.md) and [EVENTS.md](../EVENTS.md).

## Goals

- **G1. Services are the contract.** Every action that changes data is a service with a
  `services.yaml` entry and localized text.
- **G2. Every change is observable.** Each state change fires 1 event, whatever surface
  caused it.
- **G3. One payload shape.** The payload that ships is the payload that tests and
  integrators check, because 1 pure function builds it.
- **G4. One declared surface.** A surface that is in one registry and missing from
  another fails a test.
- **G5. One string source.** Labels and descriptions come from `services.yaml` and
  `strings.json`, so the Home Assistant UI and the generated reference agree.

## Non-goals

- A public websocket API. The commands serve the panel and the card, and can change.
- Device triggers. The integration has no per-item device for a trigger to attach to.
- A contribution API for other integrations ([IDEAS.md](../../IDEAS.md)).

## Design

### Services

| Service | Fields | Response |
|---|---|---|
| `add_item` | `name` (required), `value` | optional: `{"item_id": ...}` |
| `update_item` | `item_id` (required), `name`, `value` | none |
| `delete_item` | `item_id` (required) | none |

Each handler in `_register_services` calls 1 store method, maps its errors to a
localized `ServiceValidationError`, and awaits a coordinator refresh.

### Events

The store fires each event after its save ([store](store.md)). The names come from
`const.py` and follow `example_integration_<noun>_<verb>`.

| Event | Builder | Payload |
|---|---|---|
| `example_integration_item_created` | `events.item_created_event_data` | the spine |
| `example_integration_item_updated` | `events.item_updated_event_data` | the spine and `changed_fields` |
| `example_integration_item_deleted` | `events.item_deleted_event_data` | the spine, the last snapshot |

`events.item_event_data` builds the spine: `item_id`, `name` and `value`. The update
builder copies the list of changed fields into the payload.

### Websocket commands

`websocket_api.async_register` registers `list`, `add`, `update` and `delete` under the
domain prefix. Each mutating command calls the same store method as its service twin,
then refreshes the coordinator. `list` returns every item. An error answers with
`connection.send_error` and the codes `not_loaded`, `not_found` or `invalid_format`.

### The surface model

`api_surface.py` holds frozen dataclasses in tuples, so any renderer reads them in a fixed
order:

- `SERVICES`, and `SERVICE_NAMES` derived from it, which `async_unload_entry` iterates.
- `EVENTS` and `PAYLOAD_SPINES`. The drift test calls the real builders and compares
  their keys with the spine.
- `ENTITY_PLATFORMS`, `WEBSOCKET_COMMANDS`, `HTTP_VIEWS`, and the empty
  `DEVICE_TRIGGERS` and `OPTIONS`.
- `SURFACE_KINDS`, every kind of integration surface in Home Assistant with a status and
  a reason. The rows that say `not_applicable` or `deferred` show what is missing.

`ci/generate_api_docs.py` renders the model, `services.yaml` and `strings.json` into the
generated API reference of the docs site.

## Trade-offs

- **A declared model with a drift test** over **docs written by hand**: the model cannot
  fall behind the source without a red test, and the reference is generated from it.
- **Events fired in the store** over **events fired in each handler**: a new surface that
  calls the store is observed with no extra code.
- **Websocket commands next to services** over **the panel calling services**: a command
  returns the new item at once, with no wait for a state change.

## One-way doors

- The service names, field names and the `add_item` response key `item_id`.
- The event names and the payload keys `item_id`, `name`, `value` and `changed_fields`.
