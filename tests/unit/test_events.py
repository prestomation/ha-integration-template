"""Unit tests for the pure event-payload builders (no HA harness required)."""

from __future__ import annotations

from ex.events import (
    item_created_event_data,
    item_deleted_event_data,
    item_event_data,
    item_updated_event_data,
)

_ITEM = {"id": "abc", "name": "Shelf", "value": 3, "created": "t"}


def test_spine_carries_identity_and_snapshot():
    assert item_event_data(_ITEM) == {"item_id": "abc", "name": "Shelf", "value": 3}


def test_created_and_deleted_use_the_spine():
    assert item_created_event_data(_ITEM) == item_event_data(_ITEM)
    assert item_deleted_event_data(_ITEM) == item_event_data(_ITEM)


def test_updated_adds_changed_fields():
    payload = item_updated_event_data(_ITEM, ["value"])
    assert payload["item_id"] == "abc"
    assert payload["changed_fields"] == ["value"]


def test_updated_copies_changed_fields_list():
    changed = ["value"]
    payload = item_updated_event_data(_ITEM, changed)
    changed.append("name")
    # The payload must not alias the caller's list.
    assert payload["changed_fields"] == ["value"]


def test_payload_has_no_internal_fields():
    # The event surface intentionally omits `created` and `id`-as-`id`.
    assert "created" not in item_event_data(_ITEM)
    assert "id" not in item_event_data(_ITEM)
