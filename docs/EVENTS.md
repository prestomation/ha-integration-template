# Example Integration — events

The Example Integration fires a Home Assistant **bus event** for every meaningful
change to an item — created, updated, deleted. This is the surface automations and
other integrations build on. Events are *observations* of changes that already flow
through `ExampleStore`, so they need no separate service.

All payloads are built by **pure functions in `events.py`** (no HA imports), fired
at the **`store.py` mutation chokepoint** — so every surface (panel websocket,
service call, future integrations) is observed identically.

## Event catalog

Names follow `example_integration_<noun>_<verb>`.

| Event | Fires when |
|---|---|
| `example_integration_item_created` | an item is created |
| `example_integration_item_updated` | an item actually changes; payload adds `changed_fields` |
| `example_integration_item_deleted` | an item is removed |

## Payloads

Every item event shares a common **spine** (`events.item_event_data`):

```json
{
  "item_id": "a1b2c3d4",
  "name": "Garage shelf",
  "value": 4
}
```

`item_updated` extends it with the list of fields that changed:

```json
{
  "item_id": "a1b2c3d4",
  "name": "Garage shelf",
  "value": 7,
  "changed_fields": ["value"]
}
```

## Reacting to an event

Use a plain `event` trigger on the event name:

```yaml
automation:
  - alias: Notify when an item value changes
    trigger:
      - platform: event
        event_type: example_integration_item_updated
    condition: "{{ 'value' in trigger.event.data.changed_fields }}"
    action:
      - service: notify.notify
        data:
          message: >-
            {{ trigger.event.data.name }} is now {{ trigger.event.data.value }}
```

## Adding a new event (checklist)

1. Add the constant to `const.py` (`EVENT_ITEM_…`).
2. Add a pure builder to `events.py`.
3. Fire it at the relevant `store.py` chokepoint.
4. Document it in this file.
5. Cover it in `tests/unit/test_events.py` (payload shape) and
   `tests/component/test_services_events.py` (fires on the bus).
