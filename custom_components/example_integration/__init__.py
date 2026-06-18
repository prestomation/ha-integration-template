"""The Example Integration — a TEMPLATE for Home Assistant custom integrations.

Demonstrates the full stack around a tiny "items list" feature: a pure data
model, a persistent store that is the single mutation chokepoint, a coordinator,
a sensor platform, automation-facing services, panel websocket commands, a
sidebar panel + a Lovelace card, translations, and bus events for every state
change.

Setup wiring:
  store.load -> coordinator first refresh -> register panel + card + websocket
  -> forward the sensor platform -> register services.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from . import card, panel, websocket_api
from .const import DOMAIN, PLATFORMS
from .coordinator import ExampleCoordinator
from .models import ItemValidationError
from .store import ExampleStore

_LOGGER = logging.getLogger(__name__)

ADD_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("value", default=0): vol.Coerce(int),
    }
)
UPDATE_ITEM_SCHEMA = vol.Schema(
    {
        vol.Required("item_id"): cv.string,
        vol.Optional("name"): cv.string,
        vol.Optional("value"): vol.Coerce(int),
    }
)
DELETE_ITEM_SCHEMA = vol.Schema({vol.Required("item_id"): cv.string})

# Services registered once (module-global) and torn down when the last entry
# unloads. Listed here so teardown stays in sync with registration.
_SERVICES = ("add_item", "update_item", "delete_item")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration (config-entry only)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Example Integration from a config entry."""
    store = ExampleStore(hass)
    await store.load()

    coordinator = ExampleCoordinator(hass, entry, store)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await panel.async_register_panel(hass)
    card.async_register_card(hass)
    websocket_api.async_register(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry (and its services once the last entry is gone)."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and not hass.config_entries.async_loaded_entries(DOMAIN):
        for service in _SERVICES:
            hass.services.async_remove(DOMAIN, service)
    return unloaded


def _register_services(hass: HomeAssistant) -> None:
    """Register the automation-facing services (idempotent across reloads).

    These are the canonical contract; the panel websocket commands delegate to
    the same ``ExampleStore`` methods. Mutations refresh the coordinator so the
    sensor entities re-render.
    """

    def _coordinator() -> ExampleCoordinator:
        for entry in hass.config_entries.async_entries(DOMAIN):
            coord = getattr(entry, "runtime_data", None)
            if isinstance(coord, ExampleCoordinator):
                return coord
        raise ServiceValidationError("The Example Integration is not loaded")

    async def handle_add_item(call: ServiceCall) -> dict[str, Any]:
        coord = _coordinator()
        try:
            item = await coord.store.add_item(dict(call.data))
        except ItemValidationError as err:
            raise ServiceValidationError(str(err)) from err
        await coord.async_refresh()
        return {"item_id": item["id"]}

    async def handle_update_item(call: ServiceCall) -> None:
        coord = _coordinator()
        data = dict(call.data)
        item_id = data.pop("item_id")
        try:
            await coord.store.update_item(item_id, data)
        except KeyError:
            raise ServiceValidationError(f"Item not found: {item_id}") from None
        except ItemValidationError as err:
            raise ServiceValidationError(str(err)) from err
        await coord.async_refresh()

    async def handle_delete_item(call: ServiceCall) -> None:
        coord = _coordinator()
        try:
            await coord.store.delete_item(call.data["item_id"])
        except KeyError:
            raise ServiceValidationError(
                f"Item not found: {call.data['item_id']}"
            ) from None
        await coord.async_refresh()

    hass.services.async_register(
        DOMAIN,
        "add_item",
        handle_add_item,
        schema=ADD_ITEM_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN, "update_item", handle_update_item, schema=UPDATE_ITEM_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "delete_item", handle_delete_item, schema=DELETE_ITEM_SCHEMA
    )
