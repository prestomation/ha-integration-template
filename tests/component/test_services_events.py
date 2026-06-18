"""Component tests: services mutate the store, fire events, and drive entities."""

from __future__ import annotations

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_capture_events

from custom_components.example_integration.const import (
    DOMAIN,
    EVENT_ITEM_CREATED,
    EVENT_ITEM_DELETED,
    EVENT_ITEM_UPDATED,
)


def _entity_id(hass, unique_id: str) -> str | None:
    return er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)


def _total_state(hass):
    return hass.states.get(_entity_id(hass, f"{DOMAIN}_total_items"))


async def _add(hass, name="Shelf", value=3):
    return await hass.services.async_call(
        DOMAIN, "add_item", {"name": name, "value": value},
        blocking=True, return_response=True,
    )


async def test_add_item_fires_created_event_and_creates_sensor(hass, setup_entry):
    events = async_capture_events(hass, EVENT_ITEM_CREATED)
    result = await _add(hass, "Garage shelf", 4)
    await hass.async_block_till_done()

    item_id = result["item_id"]
    assert len(events) == 1
    assert events[0].data == {"item_id": item_id, "name": "Garage shelf", "value": 4}

    # Total sensor reflects the new item.
    assert _total_state(hass).state == "1"
    # A per-item sensor was created (unique_id anchored to the item id) with value 4.
    entity_id = _entity_id(hass, f"{DOMAIN}_item_{item_id}")
    assert entity_id is not None
    assert hass.states.get(entity_id).state == "4"


async def test_update_item_fires_updated_event_with_changed_fields(hass, setup_entry):
    result = await _add(hass, "Shelf", 1)
    item_id = result["item_id"]
    events = async_capture_events(hass, EVENT_ITEM_UPDATED)

    await hass.services.async_call(
        DOMAIN, "update_item", {"item_id": item_id, "value": 9}, blocking=True
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["item_id"] == item_id
    assert events[0].data["value"] == 9
    assert events[0].data["changed_fields"] == ["value"]


async def test_delete_item_fires_deleted_event(hass, setup_entry):
    result = await _add(hass, "Shelf", 1)
    item_id = result["item_id"]
    events = async_capture_events(hass, EVENT_ITEM_DELETED)

    await hass.services.async_call(
        DOMAIN, "delete_item", {"item_id": item_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data["item_id"] == item_id
    assert _total_state(hass).state == "0"


async def test_update_unknown_item_raises(hass, setup_entry):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "update_item", {"item_id": "nope", "value": 1}, blocking=True
        )


async def test_add_item_rejects_empty_name(hass, setup_entry):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "add_item", {"name": "   "}, blocking=True
        )
