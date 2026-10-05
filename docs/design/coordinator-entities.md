---
title: Coordinator and entities
summary: How the coordinator reads the store, and how the sensor platform keeps 1 entity per item under 1 service device.
implements:
  - custom_components/example_integration/coordinator.py
  - custom_components/example_integration/sensor.py
related: [architecture, store, events-api]
source_hash: 7d8a5d9d95f7
---

# Coordinator and entities

`ExampleCoordinator` is the read path for the entities. It polls no external service:
a refresh reads the store again and tells its listeners. The `sensor` platform shows the
items as native entities, which is the usage surface of the integration.

## Goals

- **G1. One read path.** Every entity reads the items from the coordinator, never from
  the store.
- **G2. Stable identity.** An entity keeps its `unique_id`, and so its entity id and its
  history, when its item is renamed.
- **G3. Immediate state.** After a mutation returns, each entity shows the new value.
- **G4. Localized names.** A fixed entity takes its name from `strings.json`.

## Non-goals

- Writes. The entities have no service and no control. Administration is in the panel.
- Per-item devices. One service device groups every entity of the config entry.
- Removal of an entity at run time. An entity for a deleted item becomes unavailable,
  and Home Assistant removes it on the next reload of the entry.

## Design

### The coordinator

`ExampleCoordinator` is a `DataUpdateCoordinator` with no update interval.
`_async_update_data` returns `store.list_items()`, so the `data` of the coordinator is
the item list, newest first. The coordinator keeps `entry` and `store` as attributes.
The services and the websocket commands reach the store through it.

Each mutation path awaits the `async_refresh()` of the coordinator after the store
call. The debounced `async_request_refresh()` would merge quick mutations, and a test
would then see an old state.

### The sensor platform

`sensor.async_setup_entry` adds 2 kinds of entity:

| Entity | State | Name | `unique_id` |
|---|---|---|---|
| `ExampleTotalSensor` | the number of items | `translation_key` `total_items` | `example_integration_total_items` |
| `ExampleItemSensor` | the item's `value` | the item's `name` | `example_integration_item_<id>` |

The total sensor has the attribute `total_value`, the sum of every item's value. Both
kinds have `SensorStateClass.MEASUREMENT`.

The platform keeps a set of known item ids. A coordinator listener compares it with the
current ids after each refresh and adds a sensor for each new id. An item sensor is
available only while its id is in the `data` of the coordinator.

### The service device

Each entity has the `DeviceInfo` from `sensor._device_info`: identifier
`(DOMAIN, entry_id)`, the panel title as its name, and `DeviceEntryType.SERVICE`. The
entities then share 1 device page.

## Trade-offs

- **A coordinator for local data** over **entities that read the store**: the
  coordinator gives 1 listener API and 1 refresh call for every surface.
- **Unavailable until reload** over **removal through the entity registry**: the
  platform stays small, and the stale entity shows its last name in the UI until the
  reload.
- **1 service device** over **1 device per item**: an item is not hardware, and per-item
  devices would need device triggers and a cleanup path.

## One-way doors

- The `unique_id` formats and the `total_items` translation key. Entity ids and
  history depend on them.
- The `total_value` attribute. Automations read it.
- The device identifier `(DOMAIN, entry_id)`.
