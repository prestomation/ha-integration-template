"""Diagnostics for the Example Integration.

Returns the config entry and current item store, so a bug report can include the
integration's full state. There is no sensitive data in the item model, so
nothing is redacted here — add ``async_redact_data`` with a key set if your
integration stores secrets.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import ExampleCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: ExampleCoordinator = entry.runtime_data
    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "domain": entry.domain,
        },
        "items": coordinator.store.list_items(),
    }
