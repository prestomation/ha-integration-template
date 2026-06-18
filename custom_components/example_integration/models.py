"""Pure item model for the Example Integration.

This module is **pure Python**: it MUST NOT import anything from
``homeassistant``. That keeps the data model unit-testable in isolation
(``tests/unit``) without the HA test harness — mirror this discipline for your
own domain's core logic.

An item is a plain JSON-serializable dict (never a model object in storage):

    {
        "id":      str,    # opaque, stable across renames
        "name":    str,    # 1..MAX_NAME_LENGTH chars
        "value":   int,    # MIN_VALUE..MAX_VALUE
        "created": str,    # ISO-8601 timestamp, set by the caller
    }
"""

from __future__ import annotations

import uuid
from typing import Any

from .const import MAX_NAME_LENGTH, MAX_VALUE, MIN_VALUE

# Fields a caller may set on create/update. ``id`` and ``created`` are managed.
EDITABLE_FIELDS = ("name", "value")


class ItemValidationError(ValueError):
    """Raised when item input fails validation.

    Service handlers translate this into a user-facing ``ServiceValidationError``
    at the HA boundary; the pure model stays HA-free.
    """


def _validate_name(name: Any) -> str:
    if not isinstance(name, str):
        raise ItemValidationError("name must be a string")
    name = name.strip()
    if not name:
        raise ItemValidationError("name must not be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise ItemValidationError(f"name must be at most {MAX_NAME_LENGTH} characters")
    return name


def _validate_value(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        # bool is an int subclass — reject it explicitly so True/False can't slip in.
        raise ItemValidationError("value must be an integer")
    if not MIN_VALUE <= value <= MAX_VALUE:
        raise ItemValidationError(f"value must be between {MIN_VALUE} and {MAX_VALUE}")
    return value


def build_item(data: dict[str, Any], *, created: str) -> dict[str, Any]:
    """Build a new, validated item dict from caller input.

    ``created`` is injected by the caller (the HA boundary passes an aware
    ``dt_util.now().isoformat()``) so this function stays clock-free and
    deterministic in tests.
    """
    name = _validate_name(data.get("name"))
    value = _validate_value(data.get("value", 0))
    return {
        "id": data.get("id") or uuid.uuid4().hex,
        "name": name,
        "value": value,
        "created": created,
    }


def apply_update(item: dict[str, Any], data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return ``(updated_item, changed_fields)`` for an in-place style edit.

    Only ``EDITABLE_FIELDS`` present in ``data`` are considered. ``changed_fields``
    lists the keys whose value actually changed — the events layer puts this in
    the ``item_updated`` payload so observers can react narrowly.
    """
    updated = dict(item)
    changed: list[str] = []
    for field in EDITABLE_FIELDS:
        if field not in data:
            continue
        new_value = _validate_name(data[field]) if field == "name" else _validate_value(data[field])
        if new_value != updated.get(field):
            updated[field] = new_value
            changed.append(field)
    return updated, changed
