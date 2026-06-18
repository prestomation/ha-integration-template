"""Persistent item store for the Example Integration.

This is the **single mutation chokepoint** for item data. Entities and the panel
read items via the coordinator and never mutate storage directly; all writes go
through ``add_item`` / ``update_item`` / ``delete_item`` here. Firing the bus
events at this chokepoint (rather than in the service handlers) guarantees every
surface — panel websocket, service call, future integrations — is observed
uniformly.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import events
from .const import (
    EVENT_ITEM_CREATED,
    EVENT_ITEM_DELETED,
    EVENT_ITEM_UPDATED,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .models import build_item, apply_update

_LOGGER = logging.getLogger(__name__)


class ExampleStore:
    """Loads, persists, and mutates the item map; fires lifecycle events."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        # Keyed by item id. JSON-serializable dicts only — never model objects.
        self._items: dict[str, dict[str, Any]] = {}

    async def load(self) -> None:
        """Load the stored document (empty on first run)."""
        data = await self._store.async_load()
        if data and isinstance(data.get("items"), dict):
            self._items = data["items"]
        else:
            self._items = {}

    async def _save(self) -> None:
        await self._store.async_save({"items": self._items})

    # ── Reads ────────────────────────────────────────────────────────────────
    def list_items(self) -> list[dict[str, Any]]:
        """All items, newest first."""
        return sorted(
            self._items.values(), key=lambda i: i.get("created", ""), reverse=True
        )

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        return self._items.get(item_id)

    # ── Mutations (the chokepoint) ────────────────────────────────────────────
    async def add_item(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate + persist a new item, then fire ``item_created``."""
        item = build_item(data, created=dt_util.now().isoformat())
        self._items[item["id"]] = item
        await self._save()
        self.hass.bus.async_fire(EVENT_ITEM_CREATED, events.item_created_event_data(item))
        _LOGGER.debug("Added item %s", item["id"])
        return item

    async def update_item(self, item_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Validate + persist edits, then fire ``item_updated`` if anything changed.

        Raises ``KeyError`` if the item does not exist.
        """
        existing = self._items[item_id]  # KeyError -> caller maps to a user error
        updated, changed = apply_update(existing, data)
        if not changed:
            return existing
        self._items[item_id] = updated
        await self._save()
        self.hass.bus.async_fire(
            EVENT_ITEM_UPDATED, events.item_updated_event_data(updated, changed)
        )
        _LOGGER.debug("Updated item %s (changed: %s)", item_id, changed)
        return updated

    async def delete_item(self, item_id: str) -> dict[str, Any]:
        """Remove an item, then fire ``item_deleted``.

        Raises ``KeyError`` if the item does not exist.
        """
        item = self._items.pop(item_id)  # KeyError -> caller maps to a user error
        await self._save()
        self.hass.bus.async_fire(EVENT_ITEM_DELETED, events.item_deleted_event_data(item))
        _LOGGER.debug("Deleted item %s", item_id)
        return item
