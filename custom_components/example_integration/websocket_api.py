"""Websocket commands for the Example Integration panel/card.

These are a **UI-latency optimization** layered on top of the services: the
panel and card read and mutate items over the websocket connection rather than
calling services and waiting for a state round-trip. Every mutating command
delegates to the *same* ``ExampleStore`` method the services use — never a
divergent code path. The services (see ``__init__.py``) remain the canonical,
automation-facing contract.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import ExampleCoordinator
from .models import ItemValidationError


def _coordinator(hass: HomeAssistant) -> ExampleCoordinator | None:
    for entry in hass.config_entries.async_entries(DOMAIN):
        coord = getattr(entry, "runtime_data", None)
        if isinstance(coord, ExampleCoordinator):
            return coord
    return None


@callback
def async_register(hass: HomeAssistant) -> None:
    """Register all websocket commands (idempotent across reloads)."""
    websocket_api.async_register_command(hass, ws_list_items)
    websocket_api.async_register_command(hass, ws_add_item)
    websocket_api.async_register_command(hass, ws_update_item)
    websocket_api.async_register_command(hass, ws_delete_item)


@callback
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list"})
def ws_list_items(hass, connection, msg) -> None:
    """Return all items."""
    coord = _coordinator(hass)
    items = coord.store.list_items() if coord else []
    connection.send_result(msg["id"], {"items": items})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/add",
        vol.Required("name"): str,
        vol.Optional("value", default=0): int,
    }
)
@websocket_api.async_response
async def ws_add_item(hass, connection, msg) -> None:
    """Create an item (delegates to the store)."""
    coord = _coordinator(hass)
    if coord is None:
        connection.send_error(msg["id"], "not_loaded", "Integration not loaded")
        return
    try:
        item = await coord.store.add_item({"name": msg["name"], "value": msg["value"]})
    except ItemValidationError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    await coord.async_refresh()
    connection.send_result(msg["id"], {"item": item})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/update",
        vol.Required("item_id"): str,
        vol.Optional("name"): str,
        vol.Optional("value"): int,
    }
)
@websocket_api.async_response
async def ws_update_item(hass, connection, msg) -> None:
    """Update an item (delegates to the store)."""
    coord = _coordinator(hass)
    if coord is None:
        connection.send_error(msg["id"], "not_loaded", "Integration not loaded")
        return
    data: dict[str, Any] = {k: msg[k] for k in ("name", "value") if k in msg}
    try:
        item = await coord.store.update_item(msg["item_id"], data)
    except KeyError:
        connection.send_error(msg["id"], "not_found", "Item not found")
        return
    except ItemValidationError as err:
        connection.send_error(msg["id"], "invalid_format", str(err))
        return
    await coord.async_refresh()
    connection.send_result(msg["id"], {"item": item})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/delete", vol.Required("item_id"): str}
)
@websocket_api.async_response
async def ws_delete_item(hass, connection, msg) -> None:
    """Delete an item (delegates to the store)."""
    coord = _coordinator(hass)
    if coord is None:
        connection.send_error(msg["id"], "not_loaded", "Integration not loaded")
        return
    try:
        await coord.store.delete_item(msg["item_id"])
    except KeyError:
        connection.send_error(msg["id"], "not_found", "Item not found")
        return
    await coord.async_refresh()
    connection.send_result(msg["id"], {})
