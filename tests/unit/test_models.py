"""Unit tests for the pure item model (no HA harness required)."""

from __future__ import annotations

import re

import pytest
from ex.const import MAX_NAME_LENGTH, MAX_VALUE, MIN_VALUE
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


# The messages below are part of the contract, not decoration: the service
# handlers surface them verbatim as the ServiceValidationError a user sees, so a
# test that only asserts "something was raised" would let the wrong message —
# or an empty one — ship unnoticed. `exactly()` anchors the pattern, because
# pytest's `match=` is a *search*: an unanchored pattern happily passes on a
# message with junk bolted onto either end.
def exactly(message: str) -> str:
    """A `pytest.raises(match=...)` pattern that must match the whole message."""
    return f"^{re.escape(message)}$"


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (None, "name must be a string"),
        (5, "name must be a string"),
        ("", "name must not be empty"),
        ("   ", "name must not be empty"),
    ],
)
def test_build_item_bad_name_says_why(bad, message):
    with pytest.raises(ItemValidationError, match=exactly(message)):
        build_item({"name": bad}, created="t")


@pytest.mark.parametrize("bad", [True, False, "3", 1.5, None])
def test_build_item_rejects_non_int_value(bad):
    with pytest.raises(ItemValidationError):
        build_item({"name": "x", "value": bad}, created="t")


def test_build_item_non_int_value_says_why():
    with pytest.raises(ItemValidationError, match=exactly("value must be an integer")):
        build_item({"name": "x", "value": "3"}, created="t")


def test_build_item_rejects_out_of_range_value():
    with pytest.raises(ItemValidationError):
        build_item({"name": "x", "value": 10_000_000}, created="t")


def test_build_item_out_of_range_value_says_why():
    with pytest.raises(
        ItemValidationError,
        match=exactly(f"value must be between {MIN_VALUE} and {MAX_VALUE}"),
    ):
        build_item({"name": "x", "value": MAX_VALUE + 1}, created="t")


# ── boundaries ───────────────────────────────────────────────────────────────
# The limits are inclusive on both sides. Asserting only well inside the range
# leaves `>` vs `>=` (and `<` vs `<=`) indistinguishable, so exercise the exact
# edge and the first value past it.


def test_name_at_the_length_limit_is_accepted():
    name = "n" * MAX_NAME_LENGTH
    assert build_item({"name": name}, created="t")["name"] == name


def test_name_one_over_the_length_limit_is_rejected():
    with pytest.raises(
        ItemValidationError,
        match=exactly(f"name must be at most {MAX_NAME_LENGTH} characters"),
    ):
        build_item({"name": "n" * (MAX_NAME_LENGTH + 1)}, created="t")


def test_name_length_is_measured_after_stripping():
    # Padding a maximum-length name must not push it over the limit.
    name = "n" * MAX_NAME_LENGTH
    assert build_item({"name": f"  {name}  "}, created="t")["name"] == name


@pytest.mark.parametrize(
    "value", [MIN_VALUE, MIN_VALUE + 1, 0, MAX_VALUE - 1, MAX_VALUE]
)
def test_value_at_the_limits_is_accepted(value):
    assert build_item({"name": "x", "value": value}, created="t")["value"] == value


@pytest.mark.parametrize("value", [MIN_VALUE - 1, MAX_VALUE + 1])
def test_value_outside_the_limits_is_rejected(value):
    with pytest.raises(ItemValidationError):
        build_item({"name": "x", "value": value}, created="t")


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


@pytest.mark.parametrize(
    ("data", "expected"),
    [({"value": 7}, ["value"]), ({"name": "Rack"}, ["name"])],
)
def test_apply_update_handles_one_field_at_a_time(data, expected):
    # `value` alone is the interesting half: the loop walks EDITABLE_FIELDS in
    # order and has to *skip past* an absent `name` to reach it, rather than
    # stopping at the first field the caller left out.
    item = build_item({"name": "Shelf", "value": 1}, created="t")
    updated, changed = apply_update(item, data)
    assert changed == expected
    for field, value in data.items():
        assert updated[field] == value
