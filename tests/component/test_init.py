"""Component tests: config-entry setup, services, and the total sensor."""

from __future__ import annotations

from homeassistant.helpers import entity_registry as er

from custom_components.example_integration.const import DOMAIN


def total_sensor_entity_id(hass) -> str:
    """Resolve the total sensor's entity_id via its stable unique_id."""
    reg = er.async_get(hass)
    entity_id = reg.async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_total_items")
    assert entity_id is not None
    return entity_id


async def test_setup_registers_services(hass, setup_entry):
    for service in ("add_item", "update_item", "delete_item"):
        assert hass.services.has_service(DOMAIN, service)


async def test_total_sensor_exists_and_starts_empty(hass, setup_entry):
    state = hass.states.get(total_sensor_entity_id(hass))
    assert state is not None
    assert state.state == "0"
    assert state.attributes["total_value"] == 0


async def test_unload_removes_services(hass, setup_entry):
    assert await hass.config_entries.async_unload(setup_entry.entry_id)
    await hass.async_block_till_done()
    for service in ("add_item", "update_item", "delete_item"):
        assert not hass.services.has_service(DOMAIN, service)
