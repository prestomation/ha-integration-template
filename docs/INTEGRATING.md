---
title: Integrating with the integration
summary: How automations and other integrations use the services, events and entities, for integrators.
---

# Integrate with Example Integration

Automations, scripts, voice assistants and other integrations use 2 stable surfaces:
**services** to act and **events** to observe. Do not read the storage file or call the
websocket commands. The panel and the card use those, and they can change.

The [API reference](https://prestomation.github.io/ha-integration-template/developer/api)
lists every service field, event payload and entity attribute. The site generates it
from the integration.

## Services

| Service | Use | Fields |
|---|---|---|
| `example_integration.add_item` | Create an item | `name` (required), `value` (optional integer) |
| `example_integration.update_item` | Change an item | `item_id` (required), `name`, `value` |
| `example_integration.delete_item` | Remove an item | `item_id` (required) |

`add_item` returns the new `item_id` when the call asks for a response:

```yaml
action:
  - service: example_integration.add_item
    data:
      name: Garage shelf
      value: 4
    response_variable: result
  # result.item_id holds the new id
```

Guard each call with `hass.services.has_service("example_integration", "<service>")`,
so your integration still works when this one is not installed.

## Events

[EVENTS.md](EVENTS.md) has the catalog and the payloads. Use an `event` trigger on
`example_integration_item_created`, `example_integration_item_updated` or
`example_integration_item_deleted`.

## Current state

Each item has a `sensor` entity. Its state is the item's `value`, and its `unique_id` is
stable. A total sensor holds the number of items, with the sum of the values in its
`total_value` attribute. Read these entities through the normal state API.

## Contract

- An item `id` is opaque and stays the same when the item is renamed. Use the id, not the
  name.
- A service raises `ServiceValidationError` for bad input, such as an unknown id or an
  empty name.
- The services and the websocket commands of the panel and the card use the same store
  methods. A change from any surface fires the same event.
