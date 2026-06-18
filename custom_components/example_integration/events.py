"""Pure event-payload builders for the Example Integration.

Events are the **observation surface**: every observable state change fires a
documented ``example_integration_<noun>_<verb>`` bus event. The payloads are
built by **pure functions here** (no HA imports) so tests and integrators can
assert against the exact shipped shape — it cannot drift from a separate
serialization path.

Events are fired at the ``store.py`` mutation chokepoint (not in service
handlers), so every surface — panel, service, websocket — is observed
uniformly. See docs/EVENTS.md for the catalog.
"""

from __future__ import annotations

from typing import Any


def item_event_data(item: dict[str, Any]) -> dict[str, Any]:
    """The common payload **spine** shared by every item event.

    Carries the stable identity + current snapshot. Specific events extend this
    (e.g. ``item_updated`` adds ``changed_fields``).
    """
    return {
        "item_id": item["id"],
        "name": item["name"],
        "value": item["value"],
    }


def item_created_event_data(item: dict[str, Any]) -> dict[str, Any]:
    """Payload for ``example_integration_item_created``."""
    return item_event_data(item)


def item_updated_event_data(
    item: dict[str, Any], changed_fields: list[str]
) -> dict[str, Any]:
    """Payload for ``example_integration_item_updated``.

    ``changed_fields`` lets observers react narrowly (e.g. ignore pure renames).
    """
    return {**item_event_data(item), "changed_fields": list(changed_fields)}


def item_deleted_event_data(item: dict[str, Any]) -> dict[str, Any]:
    """Payload for ``example_integration_item_deleted`` (last-known snapshot)."""
    return item_event_data(item)
