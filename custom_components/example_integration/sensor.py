"""Sensor entities for the Example Integration.

Two kinds of entity, both driven by the coordinator (the single read path):

* ``ExampleTotalSensor`` — one summary sensor: the count of items, with the sum
  of their values as an attribute. Always present.
* ``ExampleItemSensor`` — one per item, state = the item's ``value``. ``unique_id``
  is anchored to the item ``id`` so it survives renames.

The per-item entity set is reconciled on each coordinator refresh: new items add
an entity, deleted items remove theirs. This mirrors the common HA pattern of a
dynamic entity set backed by a coordinator.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PANEL_TITLE
from .coordinator import ExampleCoordinator


def _device_info(entry_id: str) -> DeviceInfo:
    """A single service device that groups every entity this integration creates.

    A local, deviceless integration still wants its entities grouped under one
    device page (the Gold ``devices`` rule). ``entry_type=SERVICE`` marks it as a
    service rather than a physical device; the identifier is anchored to the
    config entry so it is stable across restarts and renames.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=PANEL_TITLE,
        entry_type=DeviceEntryType.SERVICE,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the total sensor and a dynamically-reconciled per-item sensor set."""
    coordinator: ExampleCoordinator = entry.runtime_data

    async_add_entities([ExampleTotalSensor(coordinator)])

    known: set[str] = set()

    @callback
    def _reconcile() -> None:
        current = {item["id"] for item in coordinator.data or []}
        new_ids = current - known
        if new_ids:
            known.update(new_ids)
            async_add_entities(
                ExampleItemSensor(coordinator, item_id) for item_id in new_ids
            )
        # Entities for removed items mark themselves unavailable (see `available`)
        # and are pruned by HA when the config entry reloads.

    _reconcile()
    entry.async_on_unload(coordinator.async_add_listener(_reconcile))


class ExampleTotalSensor(CoordinatorEntity[ExampleCoordinator], SensorEntity):
    """Summary sensor: number of items (sum of values as an attribute)."""

    _attr_has_entity_name = True
    _attr_translation_key = "total_items"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ExampleCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_total_items"
        self._attr_device_info = _device_info(coordinator.entry.entry_id)

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"total_value": sum(i["value"] for i in (self.coordinator.data or []))}


class ExampleItemSensor(CoordinatorEntity[ExampleCoordinator], SensorEntity):
    """Per-item sensor: state = the item's value, name = the item's name."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:numeric"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ExampleCoordinator, item_id: str) -> None:
        super().__init__(coordinator)
        self._item_id = item_id
        # unique_id anchored to the item id -> survives renames.
        self._attr_unique_id = f"{DOMAIN}_item_{item_id}"
        self._attr_device_info = _device_info(coordinator.entry.entry_id)

    def _item(self) -> dict[str, Any] | None:
        for item in self.coordinator.data or []:
            if item["id"] == self._item_id:
                return item
        return None

    @property
    def available(self) -> bool:
        return self._item() is not None

    @property
    def name(self) -> str | None:
        item = self._item()
        return item["name"] if item else None

    @property
    def native_value(self) -> int | None:
        item = self._item()
        return item["value"] if item else None
