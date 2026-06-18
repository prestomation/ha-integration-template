"""DataUpdateCoordinator for the Example Integration.

The coordinator is the single read path for entities and the panel. It does not
poll an external service (the data is local); a refresh simply re-reads the
store and notifies listeners so entities re-render after a mutation.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .store import ExampleStore

_LOGGER = logging.getLogger(__name__)


class ExampleCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Exposes the current item list to entities; refreshed after each mutation."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, store: ExampleStore
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.entry = entry
        self.store = store

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Return the current items (local read — never raises for missing data)."""
        return self.store.list_items()
