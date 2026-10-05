---
title: Store
summary: Holds all item data in one JSON document, validates it with the pure model, and is the one place that changes it.
implements:
  - custom_components/example_integration/store.py
  - custom_components/example_integration/models.py
related: [architecture, coordinator-entities, events-api]
source_hash: 24d58784fee1
---

# Store

`ExampleStore` wraps the Home Assistant `Store` helper around one JSON document,
`.storage/example_integration`. It keeps the items in memory as plain dicts and writes
the full document after each change. Every write path goes through it: the services and
the websocket commands. It also fires the `example_integration_item_*` bus events, so a
change is visible to automations whatever surface caused it. `models.py` builds and
checks the item dicts that the store keeps.

## Goals

- **G1. One chokepoint.** Each change to an item goes through a store method that
  validates, writes, saves and fires its event.
- **G2. Durable on return.** When a mutation returns, its save is complete.
- **G3. Safe load.** A missing or malformed document loads as an empty item map, with no
  failed setup.
- **G4. Exact events.** An event fires once per real change, after the save, with the
  payload that `events.py` builds.
- **G5. Pure validation.** The rules for a valid item run without Home Assistant and
  without a clock.

## Non-goals

- Entities. The coordinator reads the store and the platform reads the coordinator. The
  store does not refresh the coordinator. The caller does.
- Migrations. `const.STORAGE_VERSION` is 1, and the store sets no migrate function.
- Concurrency control beyond the Home Assistant event loop.

## Design

### The item

`models.build_item` returns a new dict with 4 keys:

| Key | Type | Rule |
|---|---|---|
| `id` | str | The caller's `id`, else a new `uuid4` hex. Stable across renames. |
| `name` | str | Stripped, not empty, at most `const.MAX_NAME_LENGTH` characters. |
| `value` | int | From `const.MIN_VALUE` to `const.MAX_VALUE`. A bool is refused. |
| `created` | str | An ISO 8601 timestamp that the caller passes in. |

`models.apply_update` takes an item and a partial update. It reads only the keys in
`models.EDITABLE_FIELDS`, validates each one, and returns a copy of the item and the list
of fields whose value changed. A bad field raises `models.ItemValidationError`, and the
item in the store does not change.

### The document

`STORAGE_KEY` is the domain and `STORAGE_VERSION` is 1. `ExampleStore._save` writes
1 top-level key, `items`, which maps an item id to its dict. `store.load` reads `items`
if it is a dict, and uses an empty map if not.

### Reads

`list_items` returns every item, newest `created` first. `get_item` returns 1 item or
`None`. Readers get the stored dicts. A reader must not change them.

### The mutation shape

Each mutation keeps one order. It finds or builds the record, which raises `KeyError` for
an unknown id or `ItemValidationError` for bad input before any write. Then it changes
the in-memory map, awaits `_save`, fires its event and returns the record.

| Method | Event | Rule |
|---|---|---|
| `add_item` | `item_created` | Stamps `created` with `dt_util.now().isoformat()`. |
| `update_item` | `item_updated` | Returns the old item, saves nothing and fires nothing when no field changed. |
| `delete_item` | `item_deleted` | The payload is the last snapshot of the item. |

Events fire after the save, so a listener that reads the store back sees saved state.

## Trade-offs

- **Write the full document on each change** over **a delta log**: the document is small,
  and 1 write path keeps load simple.
- **Plain dicts** over **model objects**: the store, the events, the websocket replies
  and diagnostics all use the same JSON-ready shape, with no conversion.
- **Validation in the pure model** over **voluptuous only**: the service schema coerces
  types, but the bounds live in 1 place that the unit tier and the mutation gate check.

## One-way doors

- The storage key, the `items` map, and the 4 item keys. A change needs a storage
  version bump and a migration.
- The `id` format is opaque. Integrators key off it, so never derive it from the name.
