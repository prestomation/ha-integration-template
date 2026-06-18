# Integrating with the Example Integration

Other integrations, automations, scripts, and voice assistants interact with the
Example Integration through two stable surfaces: **services** (to act) and **events**
(to observe). Never reach into its storage or websocket commands.

## Services (the action surface)

| Service | Purpose | Fields |
|---|---|---|
| `example_integration.add_item` | Create an item | `name` (required), `value` (optional int) |
| `example_integration.update_item` | Change an item | `item_id` (required), `name`, `value` |
| `example_integration.delete_item` | Remove an item | `item_id` (required) |

`add_item` returns a response with the new `item_id` (call with
`return_response`):

```yaml
action:
  - service: example_integration.add_item
    data:
      name: Garage shelf
      value: 4
    response_variable: result
  # result.item_id is now available
```

## Events (the observation surface)

See [EVENTS.md](EVENTS.md) for the full catalog and payloads. Subscribe with a plain
`event` trigger on `example_integration_item_{created,updated,deleted}`.

## Reading current state

Each item is exposed as a `sensor` entity (state = its `value`, anchored to a stable
`unique_id`), plus a summary `sensor.total_items` (count, with `total_value` as an
attribute). Read these via the normal state APIs.

## Contract notes

- Item `id`s are opaque and stable across renames — key off them, not the name.
- Services raise `ServiceValidationError` for bad input (unknown id, empty name).
- The same store methods back the services and the panel/card websocket commands, so
  any surface that mutates data emits the same events.
