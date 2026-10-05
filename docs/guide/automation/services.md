# Services

Each data action is an `example_integration.*` service. Use the services in automations,
scripts and voice assistants.

| Service | Use | Fields |
|---|---|---|
| `example_integration.add_item` | Create an item | `name` (required), `value` |
| `example_integration.update_item` | Change an item | `item_id` (required), `name`, `value` |
| `example_integration.delete_item` | Remove an item | `item_id` (required) |

## Get the id of a new item

`add_item` returns the id of the new item when you ask for a response:

```yaml
action:
  - service: example_integration.add_item
    data:
      name: Garage shelf
      value: 4
    response_variable: result
  - service: example_integration.update_item
    data:
      item_id: "{{ result.item_id }}"
      value: 5
```

## Errors

A service call with bad input fails with a message in the Home Assistant language. For
example, an unknown `item_id` or an empty name fails.

## Events

Each change fires a bus event. The events are in the
[events reference](https://prestomation.github.io/ha-integration-template/developer/events).
