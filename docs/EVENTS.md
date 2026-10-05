---
title: Events reference
summary: The bus events that the integration fires, their payloads and example automations, for integrators.
---

# Events

The integration fires a Home Assistant **bus event** for each change to an item: create,
update and delete. Automations and other integrations use these events to react. An
event observes a change that already goes through `ExampleStore`, so it needs no service
of its own.

Pure functions in `events.py` build each payload. The store fires the event after it
saves the change. A change from the panel, a service call or a websocket command gives the
same event.

`api_surface.py` (`EVENTS` and `PAYLOAD_SPINES`) is the machine-readable index of this
catalog. `tests/unit/test_api_surface.py` calls the real builders and compares their keys
with the index. A payload field that the index does not describe fails the build.

## Event catalog

Names follow `example_integration_<noun>_<verb>`.

| Event | Fires when |
|---|---|
| `example_integration_item_created` | an item is created |
| `example_integration_item_updated` | a field of an item changes; the payload adds `changed_fields` |
| `example_integration_item_deleted` | an item is removed |

An update that changes no field fires no event.

## Payloads

Each item event has the same base payload (`events.item_event_data`):

```json
{
  "item_id": "a1b2c3d4",
  "name": "Garage shelf",
  "value": 4
}
```

`item_updated` adds the list of fields that changed:

```json
{
  "item_id": "a1b2c3d4",
  "name": "Garage shelf",
  "value": 7,
  "changed_fields": ["value"]
}
```

`item_deleted` holds the last values of the item before the delete.

## React to an event

Use an `event` trigger on the event name:

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

## Add a new event

1. Add the constant to `const.py` (`EVENT_ITEM_…`).
2. Add a pure builder to `events.py`.
3. Fire the event in the matching `store.py` method, after the save.
4. Add an `EventSpec` to `api_surface.EVENTS`.
5. Describe the event in this file.
6. Test the payload shape in `tests/unit/test_events.py`, and test that the event fires
   on the bus in `tests/component/test_services_events.py`.
