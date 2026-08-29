"""The single index of every surface an integrator can build on.

The integration's public API is spread across registries that have no reason to know
about each other: services registered in ``__init__.py``, bus events named in
``const.py`` with payloads built in ``events.py``, websocket commands decorated in
``websocket_api.py``, entity platforms in ``const.PLATFORMS``, and the static route
``panel.py`` registers. Nothing ties them together, so a surface can be added in one
place and forgotten everywhere else — registered but missing from the teardown list,
fired but absent from the docs, renamed on one side of a pair.

This module is that tie. It declares every surface once, the runtime *consumes* it
(``async_unload_entry`` iterates :data:`SERVICE_NAMES`), and
``tests/unit/test_api_surface.py`` fails when the source and the model disagree.

**It declares names and structure only.** Every human-readable string that Home
Assistant already localizes — service and field labels, entity names, error messages
— is resolved from ``services.yaml`` / ``strings.json`` at the point of use, so the
UI and any generated reference read from one source and cannot say different things.
Never restate that prose here. The one exception is :attr:`EventSpec.summary`: a bus
event has no Home Assistant string source, so its one-line "fires when" lives in this
table.

Pure, and deliberately *light*: it imports nothing from Home Assistant and nothing
from the integration beyond ``const``, so the fast unit tier can load it alongside
the rest of the pure core.

**Adapting this after you fork.** Add a row to :data:`SURFACE_KINDS` for any surface
kind you take on, then fill the matching table. :data:`DEVICE_TRIGGERS` and
:data:`OPTIONS` are empty on purpose and marked ``not_applicable`` below: the example
integration has neither a ``device_trigger.py`` nor an options flow. Their specs are
kept so the slot is labelled rather than missing.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import const

# ── Descriptors ──────────────────────────────────────────────────────────────
#
# Every table below is a ``tuple``, never a ``set``. Anything that renders them
# does so in order, and set iteration leaking in here would make the output differ
# between runs.


@dataclass(frozen=True, slots=True)
class Field:
    """One key in an event payload or entity attribute map."""

    name: str
    type: str = ""
    """Rendered verbatim (``"str | None"``, ``"list[str]"``); never parsed."""
    note: str = ""


@dataclass(frozen=True, slots=True)
class ServiceSpec:
    """An ``example_integration.*`` action.

    ``name`` is the one key shared by the ``hass.services.async_register`` call,
    ``services.yaml`` and ``strings.json``'s ``services`` section — all three are
    checked against it.
    """

    name: str
    admin_only: bool = False
    response: str = "none"
    """``"none"`` | ``"optional"`` | ``"only"``, mirroring ``SupportsResponse``."""


@dataclass(frozen=True, slots=True)
class EventSpec:
    """A bus event the integration fires, or one it listens for."""

    name: str
    """The ``const`` attribute's *value*, referenced — never a re-typed literal."""
    const_name: str
    """The ``const`` attribute holding it, so the model is pinned to ``const.py``."""
    direction: str
    """``"fired"`` | ``"listened"``."""
    payload: str
    """Which spine in :data:`PAYLOAD_SPINES`, or ``"none"``."""
    summary: str = ""
    """The "fires when" one-liner. Required for every fired event."""
    extra: tuple[Field, ...] = ()
    """Per-event keys merged onto the spine."""


@dataclass(frozen=True, slots=True)
class DeviceTriggerSpec:
    """A device-automation trigger wrapping one bus event.

    Unused by the example integration (see the module docstring). Kept so a fork
    that adds ``device_trigger.py`` has the shape waiting for it.
    """

    type: str
    event: str
    scope: str


@dataclass(frozen=True, slots=True)
class EntityPlatformSpec:
    """One entity platform and the state attributes its entities expose."""

    platform: str
    translation_keys: tuple[str, ...] = ()
    """Keys under ``strings.json`` → ``entity.<platform>``; empty when the platform
    names its entities from the data instead of a translation key."""
    attributes: tuple[Field, ...] = ()


@dataclass(frozen=True, slots=True)
class WebsocketSpec:
    """A panel websocket command.

    Internal: a UI-latency optimization over the equivalent service, never a
    substitute for it (see ``.amazonq/rules/architecture-and-code.md``). Modelled
    and tested so it can't drift, and so the pairing with its service is visible.
    """

    type: str
    admin_only: bool = False
    service: str | None = None
    """The ``example_integration.*`` service it delegates to, when there is one."""


@dataclass(frozen=True, slots=True)
class HttpViewSpec:
    """An HTTP route the integration registers. Internal, like the websocket."""

    name: str
    url: str
    methods: tuple[str, ...]
    requires_auth: bool = True


@dataclass(frozen=True, slots=True)
class OptionSpec:
    """A config-entry option key.

    Unused by the example integration (see the module docstring).
    """

    key: str
    in_flow: bool
    """Whether the options-flow form renders it."""


@dataclass(frozen=True, slots=True)
class SurfaceKind:
    """One of Home Assistant's integration surfaces, and this integration's stance.

    The point of this table is the rows that say *no*. Listing only what you offer
    can't tell you what you forgot; listing the whole space, with a reason attached
    to every absence, can. Adding a new kind of surface means adding a row here
    first.
    """

    kind: str
    status: str
    """``"published"`` | ``"internal"`` | ``"not_applicable"`` | ``"deferred"``."""
    note: str
    """One sentence. Required."""


STATUSES = ("published", "internal", "not_applicable", "deferred")


# ── Services ─────────────────────────────────────────────────────────────────

SERVICES: tuple[ServiceSpec, ...] = (
    ServiceSpec("add_item", response="optional"),
    ServiceSpec("update_item"),
    ServiceSpec("delete_item"),
)

#: What ``async_unload_entry`` removes. Derived, so registration and teardown
#: cannot disagree — a service added to :data:`SERVICES` is torn down for free.
SERVICE_NAMES: tuple[str, ...] = tuple(spec.name for spec in SERVICES)


# ── Event payloads ───────────────────────────────────────────────────────────
#
# One spine per payload shape, matching what the pure builders in ``events.py``
# actually return. The drift test calls those builders and compares the keys.

PAYLOAD_SPINES: dict[str, tuple[Field, ...]] = {
    "item": (
        Field("item_id", "str", "Stable id, anchored across renames."),
        Field("name", "str", "The item's display name at the time of the event."),
        Field("value", "int", "The item's numeric value at the time of the event."),
    ),
}


# ── Events ───────────────────────────────────────────────────────────────────

EVENTS: tuple[EventSpec, ...] = (
    EventSpec(
        const.EVENT_ITEM_CREATED,
        "EVENT_ITEM_CREATED",
        "fired",
        "item",
        summary="An item was added.",
    ),
    EventSpec(
        const.EVENT_ITEM_UPDATED,
        "EVENT_ITEM_UPDATED",
        "fired",
        "item",
        summary="An item's name or value changed.",
        extra=(
            Field(
                "changed_fields",
                "list[str]",
                "Which fields changed, so an observer can react narrowly.",
            ),
        ),
    ),
    EventSpec(
        const.EVENT_ITEM_DELETED,
        "EVENT_ITEM_DELETED",
        "fired",
        "item",
        summary="An item was removed. The payload is its last-known snapshot.",
    ),
)


# ── Device triggers ──────────────────────────────────────────────────────────

DEVICE_TRIGGERS: tuple[DeviceTriggerSpec, ...] = ()


# ── Entity platforms ─────────────────────────────────────────────────────────

ENTITY_PLATFORMS: tuple[EntityPlatformSpec, ...] = (
    EntityPlatformSpec(
        "sensor",
        translation_keys=("total_items",),
        attributes=(
            Field(
                "total_value",
                "int",
                "Sum of every item's value, on the total sensor.",
            ),
        ),
    ),
)


# ── Websocket commands (internal) ────────────────────────────────────────────

WEBSOCKET_COMMANDS: tuple[WebsocketSpec, ...] = (
    WebsocketSpec(f"{const.DOMAIN}/list"),
    WebsocketSpec(f"{const.DOMAIN}/add", service="add_item"),
    WebsocketSpec(f"{const.DOMAIN}/update", service="update_item"),
    WebsocketSpec(f"{const.DOMAIN}/delete", service="delete_item"),
)


# ── HTTP routes (internal) ───────────────────────────────────────────────────

HTTP_VIEWS: tuple[HttpViewSpec, ...] = (
    HttpViewSpec(
        "panel_static",
        const.PANEL_STATIC_URL,
        ("GET",),
        # Home Assistant serves registered static paths before authentication, which
        # is why only the built bundles live under this directory.
        requires_auth=False,
    ),
)


# ── Config entry options ─────────────────────────────────────────────────────

OPTIONS: tuple[OptionSpec, ...] = ()


# ── The whole surface space ──────────────────────────────────────────────────

SURFACE_KINDS: tuple[SurfaceKind, ...] = (
    SurfaceKind(
        "Actions (services)",
        "published",
        "Every operation that mutates or exports data ships as an "
        "`example_integration.*` service, which is the interoperability contract.",
    ),
    SurfaceKind(
        "Bus events",
        "published",
        "Every observable state change fires an `example_integration_<noun>_<verb>` "
        "event, built by a pure function so the shipped payload and the documented "
        "one are the same object.",
    ),
    SurfaceKind(
        "Device triggers",
        "not_applicable",
        "The example integration owns one service device grouping its entities, "
        "with no per-item devices for a trigger to hang off.",
    ),
    SurfaceKind(
        "Device conditions",
        "not_applicable",
        "Item state is readable from the per-item sensor, so a condition platform "
        "would add a second way to ask one question.",
    ),
    SurfaceKind(
        "Device actions",
        "not_applicable",
        "The services cover every operation and take an item id directly.",
    ),
    SurfaceKind(
        "Entity platforms",
        "published",
        "A `sensor` platform: one total sensor plus one per item, the usage surface "
        "as opposed to the admin panel.",
    ),
    SurfaceKind(
        "Entity attributes",
        "published",
        "The total sensor carries the summed value, so an automation can read it "
        "without calling a service.",
    ),
    SurfaceKind(
        "Config entry options",
        "not_applicable",
        "The example feature has nothing to configure, so there is no options flow.",
    ),
    SurfaceKind(
        "Config flow",
        "published",
        "A single-instance UI setup flow, with no YAML configuration.",
    ),
    SurfaceKind(
        "Websocket commands",
        "internal",
        "A latency optimization for the panel and card, delegating to the same "
        "store methods the services use.",
    ),
    SurfaceKind(
        "HTTP routes",
        "internal",
        "One static path serving the built panel and card bundles.",
    ),
    SurfaceKind(
        "Diagnostics",
        "published",
        "The config entry supports a diagnostics download for bug reports.",
    ),
    SurfaceKind(
        "Reauth / reconfigure flows",
        "not_applicable",
        "Storage is local and needs no credentials to re-establish.",
    ),
    SurfaceKind(
        "Repairs / issue registry",
        "deferred",
        "Nothing in the example feature can enter a state a user must be told to "
        "fix; add a row here when something can.",
    ),
    SurfaceKind(
        "Discovery",
        "not_applicable",
        "There is no device or service on the network to discover.",
    ),
)


def events_by_payload(payload: str) -> tuple[EventSpec, ...]:
    """Return every fired event sharing one payload shape, in declaration order."""
    return tuple(
        spec for spec in EVENTS if spec.direction == "fired" and spec.payload == payload
    )


__all__ = [
    "DEVICE_TRIGGERS",
    "ENTITY_PLATFORMS",
    "EVENTS",
    "HTTP_VIEWS",
    "OPTIONS",
    "PAYLOAD_SPINES",
    "SERVICES",
    "SERVICE_NAMES",
    "STATUSES",
    "SURFACE_KINDS",
    "WEBSOCKET_COMMANDS",
    "DeviceTriggerSpec",
    "EntityPlatformSpec",
    "EventSpec",
    "Field",
    "HttpViewSpec",
    "OptionSpec",
    "ServiceSpec",
    "SurfaceKind",
    "WebsocketSpec",
    "events_by_payload",
]
