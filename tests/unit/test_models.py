"""Unit tests for the pure item model (no HA harness required)."""

from __future__ import annotations

import pytest
from ex.models import ItemValidationError, apply_update, build_item


def test_build_item_assigns_id_and_created():
    item = build_item({"name": "Shelf", "value": 3}, created="2026-01-01T00:00:00")
    assert item["name"] == "Shelf"
    assert item["value"] == 3
    assert item["created"] == "2026-01-01T00:00:00"
    assert item["id"]  # generated


def test_build_item_defaults_value_to_zero():
    item = build_item({"name": "Shelf"}, created="2026-01-01T00:00:00")
    assert item["value"] == 0


def test_build_item_respects_supplied_id():
    item = build_item({"id": "fixed", "name": "Shelf"}, created="t")
    assert item["id"] == "fixed"


def test_build_item_strips_name():
    item = build_item({"name": "  Shelf  "}, created="t")
    assert item["name"] == "Shelf"


@pytest.mark.parametrize("bad", ["", "   ", None, 5])
def test_build_item_rejects_bad_name(bad):
    with pytest.raises(ItemValidationError):
        build_item({"name": bad}, created="t")


@pytest.mark.parametrize("bad", [True, False, "3", 1.5, None])
def test_build_item_rejects_non_int_value(bad):
    with pytest.raises(ItemValidationError):
        build_item({"name": "x", "value": bad}, created="t")


def test_build_item_rejects_out_of_range_value():
    with pytest.raises(ItemValidationError):
        build_item({"name": "x", "value": 10_000_000}, created="t")


def test_apply_update_tracks_changed_fields():
    item = build_item({"name": "Shelf", "value": 1}, created="t")
    updated, changed = apply_update(item, {"name": "Rack", "value": 2})
    assert updated["name"] == "Rack"
    assert updated["value"] == 2
    assert sorted(changed) == ["name", "value"]


def test_apply_update_no_op_returns_empty_changed():
    item = build_item({"name": "Shelf", "value": 1}, created="t")
    updated, changed = apply_update(item, {"name": "Shelf"})
    assert changed == []
    assert updated == item


def test_apply_update_ignores_unknown_and_managed_fields():
    item = build_item({"name": "Shelf", "value": 1}, created="t")
    updated, changed = apply_update(item, {"id": "hacked", "created": "x", "bogus": 1})
    assert changed == []
    assert updated["id"] == item["id"]
    assert updated["created"] == item["created"]


def test_apply_update_validates():
    item = build_item({"name": "Shelf"}, created="t")
    with pytest.raises(ItemValidationError):
        apply_update(item, {"name": ""})
